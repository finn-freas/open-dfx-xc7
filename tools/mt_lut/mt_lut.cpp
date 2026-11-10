#include <cstdio>
#include <cstdlib>
#include <string>

#include <lorina/aiger.hpp>
#include <mockturtle/algorithms/aig_resub.hpp>
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/algorithms/functional_reduction.hpp>
#include <mockturtle/algorithms/lut_mapper.hpp>
#include <mockturtle/algorithms/resubstitution.hpp>
#include <mockturtle/algorithms/rewrite.hpp>
#include <mockturtle/utils/tech_library.hpp>
#include <mockturtle/algorithms/node_resynthesis/xag_npn.hpp>
#include <mockturtle/io/aiger_reader.hpp>
#include <mockturtle/io/write_blif.hpp>
#include <mockturtle/networks/aig.hpp>
#include <mockturtle/networks/klut.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>

using namespace mockturtle;

int main( int argc, char** argv )
{
  if ( argc < 3 )
  {
    std::fprintf( stderr, "usage: %s in.aig out.blif [opt] [mode] [relax] [cuts]\n", argv[0] );
    return 2;
  }
  std::string opt = argc > 3 ? argv[3] : "none";
  std::string mode = argc > 4 ? argv[4] : "delay";
  uint32_t relax = argc > 5 ? std::atoi( argv[5] ) : 0;
  uint32_t cuts = argc > 6 ? std::atoi( argv[6] ) : 8;
  uint32_t req = argc > 7 ? std::atoi( argv[7] ) : 0;

  aig_network aig;
  if ( lorina::read_aiger( argv[1], aiger_reader( aig ) ) != lorina::return_code::success )
  {
    std::fprintf( stderr, "cannot read %s\n", argv[1] );
    return 1;
  }
  std::printf( "read: pis %u pos %u ands %u depth %u\n", aig.num_pis(), aig.num_pos(), aig.num_gates(),
               depth_view{ aig }.depth() );

  if ( opt == "fr" || opt == "all" )
  {
    functional_reduction( aig );
    aig = cleanup_dangling( aig );
  }
  if ( opt == "rw" || opt == "all" )
  {
    xag_npn_resynthesis<aig_network, aig_network, xag_npn_db_kind::aig_complete> resyn;
    exact_library_params eps;
    exact_library<aig_network> lib( resyn, eps );
    rewrite_params rps;
    rps.preserve_depth = true;
    rewrite( aig, lib, rps );
    aig = cleanup_dangling( aig );
  }
  if ( opt == "resub" || opt == "all" )
  {
    resubstitution_params rps;
    rps.max_pis = 8;
    rps.max_inserts = 2;
    rps.preserve_depth = true;
    depth_view dv{ aig };
    fanout_view fv{ dv };
    aig_resubstitution( fv, rps );
    aig = cleanup_dangling( aig );
  }
  std::printf( "opt %s: ands %u depth %u\n", opt.c_str(), aig.num_gates(), depth_view{ aig }.depth() );

  lut_map_params ps;
  ps.cut_enumeration_ps.cut_size = 6;
  ps.cut_enumeration_ps.cut_limit = cuts;
  ps.area_oriented_mapping = mode == "area";
  ps.relax_required = relax;
  ps.required_delay = req;
  ps.area_share_rounds = 2;
  ps.ela_rounds = 2;
  lut_map_stats st;
  klut_network klut = lut_map<aig_network, true>( aig, ps, &st );
  depth_view kd{ klut };
  std::printf( "RESULT luts %u depth %u\n", klut.num_gates(), kd.depth() );
  write_blif( klut, argv[2] );
  return 0;
}
