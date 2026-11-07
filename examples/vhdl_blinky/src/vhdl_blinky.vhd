library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity vhdl_blinky is
  generic (WIDTH : positive := 28);
  port (
    clk : in  std_logic;
    led : out std_logic_vector(3 downto 0)
  );
end entity;

architecture rtl of vhdl_blinky is
  signal count : unsigned(WIDTH - 1 downto 0) := (others => '0');
begin
  process (clk)
  begin
    if rising_edge(clk) then
      count <= count + 1;
    end if;
  end process;
  led <= std_logic_vector(count(WIDTH - 1 downto WIDTH - 4));
end architecture;
