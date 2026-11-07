library ieee;
use ieee.std_logic_1164.all;

package crc_pkg is
  function crc32_byte(c : std_logic_vector(31 downto 0); d : std_logic_vector(7 downto 0)) return std_logic_vector;
  function xor_fold4(v : std_logic_vector(31 downto 0)) return std_logic_vector;
end package;

package body crc_pkg is
  function crc32_byte(c : std_logic_vector(31 downto 0); d : std_logic_vector(7 downto 0)) return std_logic_vector is
    constant POLY : std_logic_vector(31 downto 0) := x"EDB88320";
    variable r : std_logic_vector(31 downto 0) := c;
  begin
    for i in 0 to 7 loop
      if (r(0) xor d(i)) = '1' then
        r := ('0' & r(31 downto 1)) xor POLY;
      else
        r := '0' & r(31 downto 1);
      end if;
    end loop;
    return r;
  end function;

  function xor_fold4(v : std_logic_vector(31 downto 0)) return std_logic_vector is
    variable r : std_logic_vector(3 downto 0) := (others => '0');
  begin
    for i in 0 to 7 loop
      r := r xor v(4 * i + 3 downto 4 * i);
    end loop;
    return r;
  end function;
end package body;
