create_pblock pblock_rm
add_cells_to_pblock [get_pblocks pblock_rm] [get_cells u_rm]
resize_pblock [get_pblocks pblock_rm] -add {SLICE_X12Y50:SLICE_X15Y149}
set_property RESET_AFTER_RECONFIG false [get_pblocks pblock_rm]
set_property SNAPPING_MODE OFF [get_pblocks pblock_rm]
