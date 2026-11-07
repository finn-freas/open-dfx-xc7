create_pblock pblock_rm
add_cells_to_pblock [get_pblocks pblock_rm] [get_cells u_rm]
resize_pblock [get_pblocks pblock_rm] -add {SLICE_X8Y100:SLICE_X11Y149 RAMB18_X0Y40:RAMB18_X0Y59 RAMB36_X0Y20:RAMB36_X0Y29 DSP48_X0Y40:DSP48_X0Y59}
set_property RESET_AFTER_RECONFIG false [get_pblocks pblock_rm]
set_property SNAPPING_MODE OFF [get_pblocks pblock_rm]
