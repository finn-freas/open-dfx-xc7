import com.xilinx.rapidwright.design.Cell;
import com.xilinx.rapidwright.design.Design;
import com.xilinx.rapidwright.design.DesignTools;
import com.xilinx.rapidwright.design.Net;
import com.xilinx.rapidwright.design.SiteInst;
import com.xilinx.rapidwright.design.SitePinInst;
import com.xilinx.rapidwright.device.BEL;
import com.xilinx.rapidwright.device.BELPin;
import com.xilinx.rapidwright.device.Device;
import com.xilinx.rapidwright.device.Node;
import com.xilinx.rapidwright.device.PIP;
import com.xilinx.rapidwright.device.Series;
import com.xilinx.rapidwright.device.Site;
import com.xilinx.rapidwright.device.SitePin;
import com.xilinx.rapidwright.device.SiteTypeEnum;
import com.xilinx.rapidwright.device.Tile;
import com.xilinx.rapidwright.edif.EDIFCellInst;
import com.xilinx.rapidwright.edif.EDIFHierCellInst;
import com.xilinx.rapidwright.edif.EDIFHierNet;
import com.xilinx.rapidwright.edif.EDIFHierPortInst;
import com.xilinx.rapidwright.edif.EDIFNetlist;
import com.xilinx.rapidwright.edif.EDIFPortInst;
import com.xilinx.rapidwright.edif.EDIFTools;
import com.xilinx.rapidwright.util.ReportRouteStatus;
import com.xilinx.rapidwright.util.ReportRouteStatusResult;

import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

// Builds a placed and routed DCP from a build/xroute/src/<name> directory
// (netlist.edf, place.txt, macros.txt, lockpins.txt, routes.txt,
// const_routes.txt, constraints.xdc), i.e. the same inputs
// vivado/build_xroute.tcl imposes through Tcl, but written directly as
// physical data so no Vivado placer/router step is involved.
//
// usage: XrouteDcp <srcdir> <out.dcp> [part]
public class XrouteDcp {
    static final String DEFAULT_PART = "xc7a35tcsg324-1";

    static List<String> tclWords(String line) {
        List<String> out = new ArrayList<>();
        int i = 0, n = line.length();
        while (i < n) {
            char c = line.charAt(i);
            if (c == ' ' || c == '\t') { i++; continue; }
            if (c == '{') {
                int depth = 1, j = i + 1;
                while (j < n && depth > 0) {
                    char d = line.charAt(j);
                    if (d == '{') depth++;
                    else if (d == '}') depth--;
                    j++;
                }
                out.add(line.substring(i + 1, j - 1));
                i = j;
            } else {
                int j = i;
                while (j < n && line.charAt(j) != ' ' && line.charAt(j) != '\t') j++;
                out.add(line.substring(i, j));
                i = j;
            }
        }
        return out;
    }

    static List<String> lines(Path p) throws Exception {
        List<String> out = new ArrayList<>();
        if (!Files.exists(p)) return out;
        for (String l : Files.readAllLines(p)) if (!l.trim().isEmpty()) out.add(l);
        return out;
    }

    static PIP findPip(Device dev, String spec, Map<String, Integer> stats) {
        String[] f = spec.split("/");
        if (f.length != 3) { stats.merge("pip_badspec", 1, Integer::sum); return null; }
        Tile t = dev.getTile(f[0]);
        if (t == null) { stats.merge("pip_notile", 1, Integer::sum); return null; }
        Integer a = t.getWireIndex(f[1]);
        Integer b = t.getWireIndex(f[2]);
        if (a == null || b == null || a < 0 || b < 0) { stats.merge("pip_nowire", 1, Integer::sum); return null; }
        PIP p = t.getPIP(a, b);
        if (p != null) return p;
        p = t.getPIP(b, a);
        if (p != null && p.isBidirectional()) {
            p = new PIP(p);
            p.setIsReversed(true);
            stats.merge("pip_reversed", 1, Integer::sum);
            return p;
        }
        stats.merge("pip_missing", 1, Integer::sum);
        return null;
    }

    static Net physNet(Design d, EDIFNetlist n, EDIFHierNet hn) {
        EDIFHierNet parent = n.getParentNet(hn);
        if (parent == null) parent = hn;
        String name = parent.getHierarchicalNetName();
        Net net = d.getNet(name);
        if (net == null) net = d.createNet(parent);
        return net;
    }

    public static void main(String[] args) throws Exception {
        Path src = Paths.get(args[0]);
        String out = args[1];
        String part = args.length > 2 ? args[2] : DEFAULT_PART;
        Map<String, Integer> stats = new LinkedHashMap<>();
        PrintWriter log = new PrintWriter(Files.newBufferedWriter(Paths.get(out + ".log")));

        Path edf = src.resolve("netlist.edf");
        String text = new String(Files.readAllBytes(edf));
        if (text.contains("(external LIB")) {
            text = text.replace("(external LIB", "(external hdi_primitives").replace("(libraryRef LIB)", "(libraryRef hdi_primitives)");
            edf = Paths.get(out + ".in.edf");
            Files.write(edf, text.getBytes());
            stats.merge("edif_lib_renamed", 1, Integer::sum);
        }
        EDIFNetlist n = EDIFTools.readEdifFile(edf);
        EDIFTools.ensureCorrectPartInEDIF(n, part);
        fixDirections(n, stats, log);
        tieFloatingMacroInputs(n, stats, log);
        n.expandMacroUnisims(Series.Series7);
        n.resetParentNetMap();
        Design d = new Design(n);
        orphanCheck(n, "after_read", log);
        Device dev = d.getDevice();

        Map<String, String[]> pkg = new HashMap<>();
        List<String> xdc = lines(src.resolve("constraints.xdc"));
        Pattern pp = Pattern.compile("PACKAGE_PIN\\s+(\\S+)\\s+IOSTANDARD\\s+(\\S+)\\s*\\}\\s*\\[get_ports\\s+(\\{[^}]*\\}|\\S+?)\\]");
        for (String l : xdc) {
            Matcher m = pp.matcher(l);
            if (m.find()) pkg.put(m.group(3).replace("{", "").replace("}", "").trim(), new String[]{m.group(1), m.group(2)});
        }

        for (String l : lines(src.resolve("macros.txt"))) {
            List<String> w = tclWords(l);
            String m = w.get(0);
            for (int i = 1; i + 1 < w.size(); i += 2) {
                String cname = m + "/" + w.get(i);
                placeOne(d, n, cname, w.get(i + 1), stats, log);
            }
        }
        for (String l : lines(src.resolve("place.txt"))) {
            List<String> w = tclWords(l);
            placeOne(d, n, w.get(0), w.get(1), stats, log);
        }

        for (EDIFCellInst ci : n.getTopCell().getCellInsts()) {
            String t = ci.getCellType().getName();
            if (!t.equals("IBUF") && !t.equals("OBUF")) continue;
            String port = null;
            for (EDIFPortInst pi : ci.getPortInsts()) {
                String pn = pi.getName();
                if ((t.equals("IBUF") && pn.equals("I")) || (t.equals("OBUF") && pn.equals("O"))) {
                    for (EDIFPortInst q : pi.getNet().getPortInsts())
                        if (q.isTopLevelPort()) port = q.getName();
                }
            }
            String[] pk = port == null ? null : pkg.get(port);
            if (pk == null) { log.println("io_unconstrained " + ci.getName() + " " + port); stats.merge("io_fail", 1, Integer::sum); continue; }
            try {
                Site site = dev.getSiteFromPackagePin(pk[0]);
                int before = stats.getOrDefault("placed", 0);
                placeOne(d, n, ci.getName(), site.getName() + "/" + (t.equals("IBUF") ? "INBUF_EN" : "OUTBUF"), stats, log);
                if (stats.getOrDefault("placed", 0) == before) throw new RuntimeException("placeOne failed at " + site);
                stats.merge("io_placed", 1, Integer::sum);
            } catch (Exception e) {
                log.println("io_fail " + ci.getName() + " " + e);
                stats.merge("io_fail", 1, Integer::sum);
            }
        }

        for (String l : lines(src.resolve("lockpins.txt"))) {
            List<String> w = tclWords(l);
            Cell c = d.getCell(w.get(0));
            if (c == null) { stats.merge("lock_nocell", 1, Integer::sum); log.println("lock_nocell " + w.get(0)); continue; }
            Map<String, String> want = new LinkedHashMap<>();
            for (String kv : w.get(1).trim().split("\\s+")) {
                String[] f = kv.split(":");
                want.put(f[1], f[0]);
            }
            for (String phys : new ArrayList<>(c.getPinMappingsP2L().keySet()))
                if (phys.matches("A[1-6]")) c.removePinMapping(phys);
            for (Map.Entry<String, String> e : want.entrySet()) c.addPinMapping(e.getKey(), e.getValue());
            stats.merge("lock_set", 1, Integer::sum);
        }

        Map<Net, List<PIP>> routed = new LinkedHashMap<>();
        for (String l : lines(src.resolve("routes.txt"))) {
            List<String> w = tclWords(l);
            EDIFHierPortInst hp = n.getHierPortInstFromName(w.get(0));
            if (hp == null) { stats.merge("route_noport", 1, Integer::sum); log.println("route_noport " + w.get(0)); continue; }
            Net net = physNet(d, n, hp.getHierarchicalNet());
            List<PIP> pips = new ArrayList<>();
            for (int i = 2; i < w.size(); i++) {
                PIP p = findPip(dev, w.get(i), stats);
                if (p == null) { log.println("pip_fail " + net.getName() + " " + w.get(i)); continue; }
                pips.add(p);
            }
            net.setPIPs(pips);
            routed.put(net, pips);
            stats.merge("route_nets", 1, Integer::sum);
        }
        for (String l : lines(src.resolve("const_routes.txt"))) {
            List<String> w = tclWords(l);
            Net net = w.get(0).equals("1") ? d.getVccNet() : d.getGndNet();
            List<PIP> pips = new ArrayList<>(net.getPIPs());
            for (int i = 2; i < w.size(); i++) {
                PIP p = findPip(dev, w.get(i), stats);
                if (p == null) { log.println("pip_fail " + net.getName() + " " + w.get(i)); continue; }
                pips.add(p);
            }
            net.setPIPs(pips);
            routed.put(net, pips);
        }

        orphanCheck(n, "after_place", log);
        n.resetParentNetMap();
        orphanCheck(n, "after_reset", log);
        for (SiteInst si : d.getSiteInsts()) {
            try { si.routeSite(); }
            catch (RuntimeException e) { stats.merge("siteroute_fail", 1, Integer::sum); log.println("siteroute_fail " + si.getName() + " " + e); }
        }
        DesignTools.createA1A6ToStaticNets(d);
        DesignTools.createMissingSitePinInsts(d);

        reconcile(d, routed, stats, log);

        for (String l : xdc) d.addXDCConstraint(l);

        ReportRouteStatusResult rrs = ReportRouteStatus.reportRouteStatus(d);
        String rs = "rrs routable " + rrs.routableNets + " fully_routed " + rrs.fullyRoutedNets + " errors " + rrs.netsWithRoutingErrors
            + " unrouted_pins " + rrs.netsWithSomeUnroutedPins + " conflicts " + rrs.netsWithResourceConflicts + " unplaced_pins " + rrs.netsWithSomeUnplacedPins
            + " gaps " + rrs.netsWithExplicitGaps + " unrouted " + rrs.unroutedNets + " nodriver " + rrs.netsWithNoDriver;
        log.println(rs);
        for (Map.Entry<String, Integer> e : stats.entrySet()) log.println("stat " + e.getKey() + " " + e.getValue());
        log.close();
        System.out.println(rs);
        System.out.println(stats);
        d.writeCheckpoint(out);
    }

    static boolean skipSite(Design d, SitePin sp) {
        SiteTypeEnum t = sp.getSite().getSiteTypeEnum();
        return t == SiteTypeEnum.TIEOFF || d.getSiteInstFromSite(sp.getSite()) == null;
    }

    static Net netOfCellPin(Design d, Cell c, String logPin) {
        if (c.getEDIFHierCellInst() == null) return null;
        EDIFHierPortInst hp = c.getEDIFHierCellInst().getPortInst(logPin);
        if (hp == null || hp.getHierarchicalNet() == null) return null;
        EDIFHierNet par = d.getNetlist().getParentNet(hp.getHierarchicalNet());
        if (par == null) return null;
        String nm = par.getHierarchicalNetName();
        if (nm.equals("GLOBAL_LOGIC1") || par.getNet().isVCC()) return d.getVccNet();
        if (nm.equals("GLOBAL_LOGIC0") || par.getNet().isGND()) return d.getGndNet();
        return d.getNet(nm);
    }

    static boolean rt(SiteInst si, Net x, BELPin a, BELPin b) {
        try { return si.routeIntraSiteNet(x, a, b); } catch (RuntimeException e) { return false; }
    }

    static boolean urt(SiteInst si, BELPin a, BELPin b) {
        try { return si.unrouteIntraSiteNet(a, b); } catch (RuntimeException e) { return false; }
    }

    static BELPin belPinOf(SiteInst si, SitePin sp) {
        try { return si.getSite().getBELPin(sp.getPinName()); } catch (RuntimeException e) { }
        try { return sp.getBELPin(si.getSiteTypeEnum()); } catch (RuntimeException e) { return null; }
    }

    static List<BELPin> netBelPins(Design d, Net x, SiteInst si, boolean outputs) {
        List<BELPin> out = new ArrayList<>();
        for (Cell c : si.getCells()) {
            if (c.getBEL() == null) continue;
            for (Map.Entry<String, String> m : c.getPinMappingsP2L().entrySet()) {
                BELPin bp = c.getBEL().getPin(m.getKey());
                if (bp == null || bp.isOutput() != outputs) continue;
                if (netOfCellPin(d, c, m.getValue()) == x) out.add(bp);
            }
        }
        return out;
    }

    static void reconcile(Design d, Map<Net, List<PIP>> routed, Map<String, Integer> stats, PrintWriter log) {
        Map<Net, Set<SitePin>> roots = new LinkedHashMap<>(), leaves = new LinkedHashMap<>();
        for (Map.Entry<Net, List<PIP>> e : routed.entrySet()) {
            Set<Node> ends = new HashSet<>(), starts = new HashSet<>();
            for (PIP p : e.getValue()) { starts.add(p.getStartNode()); ends.add(p.getEndNode()); }
            Set<SitePin> r = new java.util.LinkedHashSet<>(), lv = new java.util.LinkedHashSet<>();
            for (Node s : starts) {
                if (ends.contains(s)) continue;
                SitePin sp = s.getSitePin();
                if (sp != null && !skipSite(d, sp)) r.add(sp);
            }
            for (Node t : ends) {
                SitePin sp = t.getSitePin();
                if (sp != null && !skipSite(d, sp)) lv.add(sp);
            }
            roots.put(e.getKey(), r);
            leaves.put(e.getKey(), lv);
        }
        for (Net x : routed.keySet()) {
            if (x.isStaticNet()) continue;
            Set<String> want = new HashSet<>();
            for (SitePin sp : roots.get(x)) want.add(sp.getSite().getName() + "/" + sp.getPinName());
            for (SitePin sp : leaves.get(x)) want.add(sp.getSite().getName() + "/" + sp.getPinName());
            for (SitePinInst spi : new ArrayList<>(x.getPins())) {
                if (want.contains(spi.getSiteInst().getSiteName() + "/" + spi.getName())) continue;
                SiteInst si = spi.getSiteInst();
                BELPin pb = spi.getBELPin();
                for (BELPin bp : netBelPins(d, x, si, spi.isOutPin())) {
                    if (spi.isOutPin()) urt(si, bp, pb); else urt(si, pb, bp);
                }
                x.removePin(spi); spi.getSiteInst().removePin(spi);
                stats.merge(spi.isOutPin() ? "extra_outpin_removed" : "extra_inpin_removed", 1, Integer::sum);
                log.println("extra_pin_removed " + x.getName() + " " + spi);
            }
        }
        for (Net x : routed.keySet()) {
            for (SitePin sp : roots.get(x)) {
                SiteInst si = d.getSiteInstFromSite(sp.getSite());
                SitePinInst spi = si.getSitePinInst(sp.getPinName());
                BELPin pb = belPinOf(si, sp);
                if (spi != null && spi.getNet() == x) continue;
                if (spi != null) {
                    Net y = spi.getNet();
                    for (BELPin bp : netBelPins(d, y, si, true)) urt(si, bp, pb);
                    y.removePin(spi); spi.getSiteInst().removePin(spi);
                    stats.merge("outpin_taken_from_other", 1, Integer::sum);
                    log.println("outpin_taken " + x.getName() + " " + sp + " from " + y.getName());
                }
                boolean ok = x.isStaticNet();
                if (!ok && pb != null) for (BELPin bp : netBelPins(d, x, si, true)) ok |= rt(si, x, bp, pb);
                if (!ok) { stats.merge("outpin_noroute", 1, Integer::sum); log.println("outpin_noroute " + x.getName() + " " + sp); }
                try { x.createPin(sp.getPinName(), si); stats.merge("outpin_added", 1, Integer::sum); }
                catch (RuntimeException ex) { stats.merge("pin_invalid", 1, Integer::sum); log.println("pin_invalid " + x.getName() + " " + sp + " " + ex.getMessage()); }
            }
        }
        for (Net x : routed.keySet()) {
            for (SitePin sp : leaves.get(x)) {
                SiteInst si = d.getSiteInstFromSite(sp.getSite());
                SitePinInst spi = si.getSitePinInst(sp.getPinName());
                BELPin pb = belPinOf(si, sp);
                if (spi != null && spi.getNet() != x) {
                    Net y = spi.getNet();
                    if (pb != null) for (BELPin bp : netBelPins(d, y, si, false)) urt(si, pb, bp);
                    y.removePin(spi); spi.getSiteInst().removePin(spi);
                    stats.merge("inpin_taken_from_" + (y.isStaticNet() ? "static" : "other"), 1, Integer::sum);
                    log.println("inpin_taken " + x.getName() + " " + sp + " from " + y.getName());
                    spi = null;
                }
                if (spi == null) {
                    try { x.createPin(sp.getPinName(), si); stats.merge("inpin_added", 1, Integer::sum); }
                    catch (RuntimeException ex) { stats.merge("pin_invalid", 1, Integer::sum); log.println("pin_invalid " + x.getName() + " " + sp + " " + ex.getMessage()); continue; }
                }
                if (x.isStaticNet() || pb == null) continue;
                for (BELPin bp : netBelPins(d, x, si, false)) {
                    Net cur = si.getNetFromSiteWire(bp.getSiteWireName());
                    if (cur == x) continue;
                    if (rt(si, x, pb, bp)) stats.merge("inpin_routed", 1, Integer::sum);
                }
            }
        }
    }

    static void tieFloatingMacroInputs(EDIFNetlist n, Map<String, Integer> stats, PrintWriter log) {
        Set<String> macros = new HashSet<>();
        for (com.xilinx.rapidwright.edif.EDIFCell c : Design.getMacroPrimitives(Series.Series7).getCells()) macros.add(c.getName());
        com.xilinx.rapidwright.edif.EDIFNet gnd = null;
        for (EDIFCellInst ci : n.getTopCell().getCellInsts()) {
            if (!macros.contains(ci.getCellType().getName())) continue;
            for (com.xilinx.rapidwright.edif.EDIFPort p : ci.getCellType().getPorts()) {
                if (!p.isInput()) continue;
                int w = p.getWidth();
                for (int i = 0; i < w; i++) {
                    String nm = p.isBus() ? p.getBusName() + "[" + i + "]" : p.getName();
                    EDIFPortInst have = ci.getPortInst(nm);
                    if (have != null && have.getNet() != null) continue;
                    if (gnd == null) gnd = EDIFTools.getStaticNet(com.xilinx.rapidwright.design.NetType.GND, n.getTopCell(), n);
                    if (have != null) { gnd.addPortInst(have); stats.merge("macro_input_tied_gnd_existing", 1, Integer::sum); log.println("macro_input_tied_gnd_existing " + ci.getName() + " " + nm); continue; }
                    EDIFPortInst pi = p.isBus() ? gnd.createPortInst(p, w - 1 - i, ci) : gnd.createPortInst(p, ci);
                    stats.merge("macro_input_tied_gnd", 1, Integer::sum);
                    log.println("macro_input_tied_gnd " + ci.getName() + " " + nm + " -> " + pi.getName());
                }
            }
        }
    }

    static void fixDirections(EDIFNetlist n, Map<String, Integer> stats, PrintWriter log) {
        for (com.xilinx.rapidwright.edif.EDIFCell c : n.getHDIPrimitivesLibrary().getCells()) {
            com.xilinx.rapidwright.edif.EDIFCell ref = null;
            try { ref = Design.getUnisimCell(com.xilinx.rapidwright.design.Unisim.valueOf(c.getName())); } catch (RuntimeException e) { }
            if (ref == null) { log.println("dir_nounisim " + c.getName()); stats.merge("dir_nounisim", 1, Integer::sum); continue; }
            for (com.xilinx.rapidwright.edif.EDIFPort rp : ref.getPorts()) {
                String bn = rp.isBus() ? rp.getBusName() : rp.getName();
                boolean has = false;
                for (com.xilinx.rapidwright.edif.EDIFPort p : c.getPorts()) {
                    String b = p.getName();
                    int k = b.indexOf('[');
                    if (k >= 0) b = b.substring(0, k);
                    if (b.equals(bn)) has = true;
                }
                if (!has) { c.createPort(rp); stats.merge("port_added", 1, Integer::sum); log.println("port_added " + c.getName() + " " + rp.getName()); }
            }
            for (com.xilinx.rapidwright.edif.EDIFPort p : new ArrayList<>(c.getPorts())) {
                String base = p.getName();
                int k = base.indexOf('[');
                if (k >= 0) base = base.substring(0, k);
                com.xilinx.rapidwright.edif.EDIFPort rp = ref.getPort(base);
                if (rp == null) { log.println("dir_noport " + c.getName() + " " + p.getName()); stats.merge("dir_noport", 1, Integer::sum); continue; }
                if (p.getDirection() != rp.getDirection()) { p.setDirection(rp.getDirection()); stats.merge("dir_fixed", 1, Integer::sum); }
            }
        }
    }

    static void orphanCheck(EDIFNetlist n, String tag, PrintWriter log) {
        int miss = 0, tot = 0;
        String ex = "";
        for (com.xilinx.rapidwright.edif.EDIFNet en : n.getTopCell().getNets()) {
            EDIFHierNet hn = new EDIFHierNet(n.getTopHierCellInst(), en);
            tot++;
            if (n.getParentNet(hn) == null) { miss++; if (ex.length() < 300) ex += " " + en.getName(); }
        }
        log.println("orphan " + tag + " " + miss + " of " + tot + ex);
        log.flush();
    }

    static void ensurePin(Design d, Net net, SitePin sp, Map<String, Integer> stats, PrintWriter log, boolean source) {
        SiteInst si = d.getSiteInstFromSite(sp.getSite());
        if (si == null) { stats.merge("pin_nosite", 1, Integer::sum); log.println("pin_nosite " + net.getName() + " " + sp); return; }
        SitePinInst spi = si.getSitePinInst(sp.getPinName());
        if (spi != null) {
            if (spi.getNet() != net) {
                stats.merge(source ? "srcpin_othernet" : "pin_othernet", 1, Integer::sum);
                log.println((source ? "srcpin_othernet " : "pin_othernet ") + net.getName() + " " + sp + " has " + spi.getNet());
            }
            return;
        }
        try { net.createPin(sp.getPinName(), si); }
        catch (RuntimeException e) { stats.merge("pin_invalid", 1, Integer::sum); log.println("pin_invalid " + net.getName() + " " + sp + " " + e.getMessage()); return; }
        stats.merge(source ? "srcpin_added" : "pin_added", 1, Integer::sum);
        log.println((source ? "srcpin_added " : "pin_added ") + net.getName() + " " + sp);
    }

    static void placeOne(Design d, EDIFNetlist n, String cname, String loc, Map<String, Integer> stats, PrintWriter log) {
        EDIFHierCellInst hi = n.getHierCellInstFromName(cname);
        if (hi == null) { stats.merge("place_nocell", 1, Integer::sum); log.println("place_nocell " + cname); return; }
        String[] sb = loc.split("/");
        Site site = d.getDevice().getSite(sb[0]);
        if (site == null) { stats.merge("place_nosite", 1, Integer::sum); log.println("place_nosite " + cname + " " + loc); return; }
        List<SiteTypeEnum> types = new ArrayList<>();
        SiteInst have = d.getSiteInstFromSite(site);
        if (have != null) types.add(have.getSiteTypeEnum());
        else {
            types.add(site.getSiteTypeEnum());
            for (SiteTypeEnum alt : site.getAlternateSiteTypeEnums()) types.add(alt);
        }
        for (SiteTypeEnum st : types) {
            SiteInst si = d.getSiteInstFromSite(site);
            boolean fresh = false;
            if (si == null) { si = d.createSiteInst(site.getName(), st, site); fresh = true; }
            BEL bel = sb.length > 1 ? si.getBEL(sb[1]) : null;
            if (bel == null) bel = si.getBEL(st.toString());
            if (bel == null && sb.length == 1) bel = si.getBELs()[0];
            Cell c = null;
            if (bel != null) {
                try { c = si.createCell(hi, bel); }
                catch (RuntimeException e) { log.println("place_try " + cname + " " + loc + " " + st + " " + e.getMessage()); c = null; }
            }
            if (c != null && c.getBEL() != null) {
                stats.merge("placed", 1, Integer::sum);
                if (st != site.getSiteTypeEnum()) stats.merge("placed_type_" + st, 1, Integer::sum);
                return;
            }
            if (fresh) d.removeSiteInst(si);
        }
        stats.merge("place_fail", 1, Integer::sum);
        log.println("place_fail " + cname + " " + loc);
    }
}
