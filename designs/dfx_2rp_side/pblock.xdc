create_pblock pblock_rp1
add_cells_to_pblock [get_pblocks pblock_rp1] [get_cells u_rp1]
resize_pblock [get_pblocks pblock_rp1] -add {SLICE_X12Y100:SLICE_X13Y149}
set_property RESET_AFTER_RECONFIG false [get_pblocks pblock_rp1]
set_property SNAPPING_MODE OFF [get_pblocks pblock_rp1]
create_pblock pblock_rp2
add_cells_to_pblock [get_pblocks pblock_rp2] [get_cells u_rp2]
resize_pblock [get_pblocks pblock_rp2] -add {SLICE_X14Y100:SLICE_X15Y149}
set_property RESET_AFTER_RECONFIG false [get_pblocks pblock_rp2]
set_property SNAPPING_MODE OFF [get_pblocks pblock_rp2]
