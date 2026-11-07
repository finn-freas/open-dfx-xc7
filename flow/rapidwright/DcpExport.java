import com.xilinx.rapidwright.design.Cell;
import com.xilinx.rapidwright.design.Design;
import com.xilinx.rapidwright.design.Net;
import com.xilinx.rapidwright.design.SiteInst;
import com.xilinx.rapidwright.design.SitePinInst;
import com.xilinx.rapidwright.device.PIP;
import com.xilinx.rapidwright.device.SitePIP;

import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Map;

// Dumps the exact physical implementation of a DCP: every placed cell
// (site, BEL, site type, physical->logical pin map), every net's PIPs
// (tile/wire0/wire1, '<' marks a reversed bidirectional PIP), its site pins,
// and every used site PIP with the net on it.
//
// usage: DcpExport <in.dcp> <outdir>
public class DcpExport {
    public static void main(String[] args) throws Exception {
        Design d = args.length > 2 ? Design.readCheckpoint(args[0], args[2]) : Design.readCheckpoint(args[0]);
        Files.createDirectories(Paths.get(args[1]));
        int nc = 0, nn = 0, np = 0, ns = 0;
        try (PrintWriter f = new PrintWriter(Files.newBufferedWriter(Paths.get(args[1], "cells.tsv")))) {
            for (Cell c : d.getCells()) {
                if (c.getSite() == null || c.getBEL() == null) continue;
                StringBuilder pm = new StringBuilder();
                StringBuilder sw = new StringBuilder();
                for (Map.Entry<String, String> e : c.getPinMappingsP2L().entrySet()) {
                    com.xilinx.rapidwright.device.BELPin bp = c.getBEL().getPin(e.getKey());
                    if (bp == null || !bp.isOutput()) continue;
                    Net on = c.getSiteInst().getNetFromSiteWire(bp.getSiteWireName());
                    if (sw.length() > 0) sw.append(',');
                    sw.append(e.getValue()).append(':').append(bp.getSiteWireName()).append(':').append(on == null ? "" : on.getName());
                }
                for (Map.Entry<String, String> e : c.getPinMappingsP2L().entrySet()) {
                    if (pm.length() > 0) pm.append(',');
                    pm.append(e.getKey()).append(':').append(e.getValue());
                }
                f.println(c.getName() + "\t" + c.getType() + "\t" + c.getSite().getName() + "\t" + c.getBEL().getName() + "\t"
                    + c.getSiteInst().getSiteTypeEnum() + "\t" + (c.isRoutethru() ? 1 : 0) + "\t" + pm + "\t" + sw);
                nc++;
            }
        }
        try (PrintWriter f = new PrintWriter(Files.newBufferedWriter(Paths.get(args[1], "nets.tsv")));
             PrintWriter g = new PrintWriter(Files.newBufferedWriter(Paths.get(args[1], "pins.tsv")))) {
            for (Net n : d.getNets()) {
                StringBuilder sb = new StringBuilder(n.getName());
                sb.append('\t').append(n.getType());
                for (PIP p : n.getPIPs()) {
                    sb.append('\t').append(p.getTile().getName()).append('/').append(p.getStartWireName())
                      .append(p.isReversed() ? "<" : "/").append(p.getEndWireName());
                    np++;
                }
                f.println(sb);
                for (SitePinInst spi : n.getPins())
                    g.println(n.getName() + "\t" + spi.getSiteInst().getSiteName() + "\t" + spi.getName() + "\t" + (spi.isOutPin() ? "out" : "in")
                        + "\t" + spi.getSite().getTile().getName() + "\t" + spi.getSite().getTileWireNameFromPinName(spi.getName())
                        + "\t" + (spi.getBELPin() == null ? "" : spi.getBELPin().getSiteWireName()));
                nn++;
            }
        }
        try (PrintWriter f = new PrintWriter(Files.newBufferedWriter(Paths.get(args[1], "sitepips.tsv")))) {
            for (SiteInst si : d.getSiteInsts()) {
                for (SitePIP sp : si.getUsedSitePIPs()) {
                    Net n = si.getNetFromSiteWire(sp.getInputPin().getSiteWireName());
                    f.println(si.getSiteName() + "\t" + si.getSiteTypeEnum() + "\t" + sp.getBELName() + "\t" + sp.getInputPinName()
                        + "\t" + sp.getOutputPinName() + "\t" + (n == null ? "" : n.getName())
                        + "\t" + sp.getInputPin().getSiteWireName() + "\t" + sp.getOutputPin().getSiteWireName());
                    ns++;
                }
            }
        }
        System.out.println("cells " + nc + " nets " + nn + " pips " + np + " sitepips " + ns);
    }
}
