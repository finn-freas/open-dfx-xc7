library ieee;
use ieee.std_logic_1164.all;

entity rm_core is
  port (
    valid : in  std_logic;
    funct : in  std_logic_vector(9 downto 0);
    rs1   : in  std_logic_vector(31 downto 0);
    rs2   : in  std_logic_vector(31 downto 0);
    rd    : out std_logic_vector(31 downto 0);
    ready : out std_logic
  );
end entity;

architecture rtl of rm_core is
begin
  rd    <= (rs1 or not rs2) when funct(0) = '1' else (rs1 and not rs2);
  ready <= valid;
end architecture;
