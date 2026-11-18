import java.io.IOException;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CharsetDecoder;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Starsector CSV reader/writer.
 * Reads the game's mixed UTF-8 / Windows-1252 bytes, then parses RFC 4180
 * records (quotes, doubled quotes, embedded newlines). Comment rows are
 * ordinary records whose first cell starts with '#'; they are preserved.
 */
public class SsCsv {
    private static final int[] CP1252 = new int[32];
    static {
        int[] extra = {
            0x20AC, 0x0081, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021,
            0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0x008D, 0x017D, 0x008F,
            0x0090, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014,
            0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x009D, 0x017E, 0x0178
        };
        System.arraycopy(extra, 0, CP1252, 0, 32);
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("usage: SsCsv dump|write|dump-tree ...");
            System.exit(2);
        }
        switch (args[0]) {
            case "dump" -> dump(Path.of(args[1]), Path.of(args[2]));
            case "write" -> write(Path.of(args[1]), Path.of(args[2]));
            case "dump-tree" -> dumpTree(Path.of(args[1]), Path.of(args[2]), args[3]);
            default -> throw new IllegalArgumentException(args[0]);
        }
    }

    /** args: root outDir comma-separated relative paths */
    static void dumpTree(Path root, Path outDir, String rels) throws Exception {
        Files.createDirectories(outDir);
        int n = 0;
        for (String rel : rels.split(",")) {
            if (rel.isBlank()) continue;
            Path in = root.resolve(rel);
            Path out = outDir.resolve(rel + ".json");
            Files.createDirectories(out.getParent());
            dump(in, out);
            n++;
        }
        System.out.println("dumped " + n);
    }

    static void dump(Path in, Path out) throws Exception {
        byte[] raw = Files.readAllBytes(in);
        String nl = detectNewline(raw);
        String text = decode(raw);
        List<List<String>> rows = parse(text);
        JSONObject root = new JSONObject();
        root.put("nl", nl);
        root.put("badBytes", countBad(raw));
        JSONArray arr = new JSONArray();
        for (List<String> row : rows) {
            JSONArray cells = new JSONArray();
            for (String c : row) cells.put(c);
            arr.put(cells);
        }
        root.put("rows", arr);
        Files.createDirectories(out.getParent() == null ? Path.of(".") : out.getParent());
        Files.writeString(out, root.toString());
    }

    static void write(Path in, Path out) throws Exception {
        JSONObject root = new JSONObject(Files.readString(in));
        String nl = root.optString("nl", "\n");
        JSONArray rows = root.getJSONArray("rows");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < rows.length(); i++) {
            JSONArray cells = rows.getJSONArray(i);
            for (int c = 0; c < cells.length(); c++) {
                if (c > 0) sb.append(',');
                sb.append(quote(cells.getString(c), c == 0));
            }
            sb.append(nl);
        }
        Files.createDirectories(out.getParent() == null ? Path.of(".") : out.getParent());
        Files.writeString(out, sb.toString(), StandardCharsets.UTF_8);
    }

    static String detectNewline(byte[] raw) {
        int crlf = 0, lf = 0;
        for (int i = 0; i < raw.length; i++) {
            if (raw[i] == '\n') {
                if (i > 0 && raw[i - 1] == '\r') crlf++;
                else lf++;
            }
        }
        return crlf >= lf ? "\r\n" : "\n";
    }

    static int countBad(byte[] data) {
        int bad = 0;
        int i = 0;
        while (i < data.length) {
            int b = data[i] & 0xFF;
            if (b < 0x80) { i++; continue; }
            int need = b >= 0xF0 ? 4 : b >= 0xE0 ? 3 : b >= 0xC2 ? 2 : 0;
            if (need == 0 || i + need > data.length || !continuation(data, i, need) || !utf8(data, i, need)) {
                bad++;
                i++;
                continue;
            }
            i += need;
        }
        return bad;
    }

    static String decode(byte[] data) {
        StringBuilder sb = new StringBuilder(data.length + 16);
        int i = 0;
        while (i < data.length) {
            int b = data[i] & 0xFF;
            if (b < 0x80) {
                sb.append((char) b);
                i++;
                continue;
            }
            int need = b >= 0xF0 ? 4 : b >= 0xE0 ? 3 : b >= 0xC2 ? 2 : 0;
            if (need > 0 && i + need <= data.length && continuation(data, i, need) && utf8(data, i, need)) {
                sb.append(new String(data, i, need, StandardCharsets.UTF_8));
                i += need;
            } else {
                sb.append((char) (b >= 0x80 && b <= 0x9F ? CP1252[b - 0x80] : b));
                i++;
            }
        }
        if (sb.length() > 0 && sb.charAt(0) == '\uFEFF') sb.deleteCharAt(0);
        return sb.toString();
    }

    static boolean continuation(byte[] data, int i, int need) {
        for (int k = 1; k < need; k++) {
            if ((data[i + k] & 0xC0) != 0x80) return false;
        }
        return true;
    }

    static boolean utf8(byte[] data, int i, int need) {
        try {
            CharsetDecoder dec = StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT);
            dec.decode(ByteBuffer.wrap(data, i, need));
            return true;
        } catch (CharacterCodingException e) {
            return false;
        }
    }

    static List<List<String>> parse(String text) {
        List<List<String>> rows = new ArrayList<>();
        int n = text.length();
        int i = 0;
        while (i < n) {
            List<String> row = new ArrayList<>();
            StringBuilder cell = new StringBuilder();
            boolean inQuotes = false;
            boolean started = false;
            while (i < n) {
                char ch = text.charAt(i);
                if (inQuotes) {
                    if (ch == '"') {
                        if (i + 1 < n && text.charAt(i + 1) == '"') {
                            cell.append('"');
                            i += 2;
                        } else {
                            inQuotes = false;
                            i++;
                        }
                    } else {
                        cell.append(ch);
                        i++;
                    }
                } else if (ch == '"' && !started) {
                    inQuotes = true;
                    started = true;
                    i++;
                } else if (ch == '"') {
                    // quote after content: keep, matching lenient game/python cases
                    cell.append(ch);
                    started = true;
                    i++;
                } else if (ch == ',') {
                    row.add(cell.toString());
                    cell.setLength(0);
                    started = false;
                    i++;
                } else if (ch == '\n') {
                    i++;
                    break;
                } else if (ch == '\r') {
                    i++;
                    if (i < n && text.charAt(i) == '\n') i++;
                    break;
                } else {
                    cell.append(ch);
                    started = true;
                    i++;
                }
            }
            // unfinished quoted field at EOF still closes
            if (i >= n && (started || cell.length() > 0 || !row.isEmpty())) {
                row.add(cell.toString());
                rows.add(row);
                break;
            }
            row.add(cell.toString());
            // skip a trailing empty record caused by a final newline
            if (i >= n && row.size() == 1 && row.get(0).isEmpty()) break;
            rows.add(row);
        }
        return rows;
    }

    static String quote(String value) {
        return quote(value, false);
    }

    static String quote(String value, boolean first) {
        boolean need = false;
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            if (ch == ',' || ch == '"' || ch == '\n' || ch == '\r') {
                need = true;
                break;
            }
        }
        // A row whose first character is '#' is dropped by the game's CSV parser.
        // Do not quote a leading '#' or the row becomes a real record.
        // Trailing spaces still need quotes, except on that comment cell.
        if (!need && (value.startsWith(" ") || value.endsWith(" "))) {
            if (!(first && value.startsWith("#"))) need = true;
        }
        if (!need) return value;
        StringBuilder sb = new StringBuilder(value.length() + 2);
        sb.append('"');
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            if (ch == '"') sb.append("\"\"");
            else sb.append(ch);
        }
        sb.append('"');
        return sb.toString();
    }
}
