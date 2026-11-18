import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.tree.AbstractInsnNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.LdcInsnNode;
import org.objectweb.asm.tree.MethodNode;

/**
 * Dump or patch user-visible String constants inside a jar.
 * Patching rewrites LDC operands and repacks the jar. Obfuscated classes are
 * not recompiled; stack maps stay intact because only the constant changes.
 */
public class SsJar {
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("usage: SsJar dump|patch ...");
            System.exit(2);
        }
        switch (args[0]) {
            case "dump" -> dump(Path.of(args[1]), Path.of(args[2]));
            case "patch" -> patch(Path.of(args[1]), Path.of(args[2]), Path.of(args[3]));
            default -> throw new IllegalArgumentException(args[0]);
        }
    }

    record Hit(String cls, String method, String desc, int index, String text) {}

    static List<Hit> stringsOf(byte[] bytes) {
        ClassReader cr = new ClassReader(bytes);
        ClassNode cn = new ClassNode();
        cr.accept(cn, 0);
        List<Hit> hits = new ArrayList<>();
        for (MethodNode mn : cn.methods) {
            if (mn.instructions == null) continue;
            int index = 0;
            for (AbstractInsnNode insn = mn.instructions.getFirst(); insn != null; insn = insn.getNext()) {
                if (insn instanceof LdcInsnNode ldc && ldc.cst instanceof String s) {
                    hits.add(new Hit(cn.name, mn.name, mn.desc, index, s));
                    index++;
                }
            }
        }
        return hits;
    }

    static void dump(Path jar, Path out) throws Exception {
        StringBuilder sb = new StringBuilder();
        try (JarFile jf = new JarFile(jar.toFile())) {
            Enumeration<JarEntry> en = jf.entries();
            while (en.hasMoreElements()) {
                JarEntry e = en.nextElement();
                if (!e.getName().endsWith(".class")) continue;
                byte[] bytes;
                try (InputStream in = jf.getInputStream(e)) {
                    bytes = in.readAllBytes();
                }
                try {
                    for (Hit h : stringsOf(bytes)) {
                        sb.append(json(h)).append('\n');
                    }
                } catch (Exception ex) {
                    System.err.println("skip " + e.getName() + " " + ex.getMessage());
                }
            }
        }
        Files.createDirectories(out.getParent());
        Files.writeString(out, sb.toString(), StandardCharsets.UTF_8);
        System.out.println("wrote " + out);
    }

    static String json(Hit h) {
        return "{\"c\":" + q(h.cls) + ",\"m\":" + q(h.method) + ",\"d\":" + q(h.desc)
                + ",\"i\":" + h.index + ",\"t\":" + q(h.text) + "}";
    }

    static String q(String s) {
        StringBuilder sb = new StringBuilder(s.length() + 2);
        sb.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '\\' -> sb.append("\\\\");
                case '"' -> sb.append("\\\"");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> {
                    if (c < 0x20) sb.append(String.format("\\u%04x", (int) c));
                    else sb.append(c);
                }
            }
        }
        sb.append('"');
        return sb.toString();
    }

    /** replacements file: jsonl {c,m,d,i,zh} */
    static void patch(Path inJar, Path replFile, Path outJar) throws Exception {
        Map<String, String> map = new HashMap<>();
        for (String line : Files.readAllLines(replFile, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            String c = field(line, "c");
            String m = field(line, "m");
            String d = field(line, "d");
            String i = field(line, "i");
            String zh = field(line, "zh");
            map.put(c + "\0" + m + "\0" + d + "\0" + i, zh);
        }
        int replaced = 0;
        try (JarFile jf = new JarFile(inJar.toFile());
             JarOutputStream jos = new JarOutputStream(Files.newOutputStream(outJar))) {
            Enumeration<JarEntry> en = jf.entries();
            while (en.hasMoreElements()) {
                JarEntry e = en.nextElement();
                byte[] bytes;
                try (InputStream in = jf.getInputStream(e)) {
                    bytes = in.readAllBytes();
                }
                if (e.getName().endsWith(".class")) {
                    byte[] patched = patchClass(bytes, map);
                    if (patched != null) {
                        bytes = patched;
                        replaced++;
                    }
                }
                JarEntry out = new JarEntry(e.getName());
                jos.putNextEntry(out);
                jos.write(bytes);
                jos.closeEntry();
            }
        }
        System.out.println("patched classes " + replaced);
    }

    static byte[] patchClass(byte[] bytes, Map<String, String> map) {
        ClassReader cr = new ClassReader(bytes);
        ClassNode cn = new ClassNode();
        cr.accept(cn, 0);
        boolean dirty = false;
        for (MethodNode mn : cn.methods) {
            if (mn.instructions == null) continue;
            int index = 0;
            for (AbstractInsnNode insn = mn.instructions.getFirst(); insn != null; insn = insn.getNext()) {
                if (insn instanceof LdcInsnNode ldc && ldc.cst instanceof String) {
                    String key = cn.name + "\0" + mn.name + "\0" + mn.desc + "\0" + index;
                    String zh = map.get(key);
                    if (zh != null && !zh.equals(ldc.cst)) {
                        ldc.cst = zh;
                        dirty = true;
                    }
                    index++;
                }
            }
        }
        if (!dirty) return null;
        ClassWriter cw = new ClassWriter(0);
        cn.accept(cw);
        return cw.toByteArray();
    }

    /** Minimal extractor for flat string fields in our own jsonl. */
    static String field(String line, String name) {
        String key = "\"" + name + "\":";
        int p = line.indexOf(key);
        if (p < 0) throw new IllegalArgumentException("missing " + name);
        int i = p + key.length();
        while (i < line.length() && line.charAt(i) == ' ') i++;
        if (i < line.length() && line.charAt(i) == '"') {
            i++;
            StringBuilder sb = new StringBuilder();
            while (i < line.length()) {
                char c = line.charAt(i);
                if (c == '\\') {
                    char n = line.charAt(++i);
                    sb.append(switch (n) {
                        case 'n' -> '\n';
                        case 'r' -> '\r';
                        case 't' -> '\t';
                        case 'u' -> {
                            int cp = Integer.parseInt(line.substring(i + 1, i + 5), 16);
                            i += 4;
                            yield (char) cp;
                        }
                        default -> n;
                    });
                    i++;
                } else if (c == '"') {
                    return sb.toString();
                } else {
                    sb.append(c);
                    i++;
                }
            }
            throw new IllegalArgumentException("unterminated " + name);
        }
        int j = i;
        while (j < line.length() && line.charAt(j) != ',' && line.charAt(j) != '}') j++;
        return line.substring(i, j).trim();
    }
}
