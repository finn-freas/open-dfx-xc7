library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity vhdl_mixed is
  port (
    clk : in  std_logic;
    led : out std_logic_vector(3 downto 0)
  );
end entity;

architecture rtl of vhdl_mixed is
  component prbs32 is
    port (
      clk : in  std_logic;
      en  : in  std_logic;
      q   : out std_logic_vector(31 downto 0)
    );
  end component;

  type state_t is (IDLE, LOAD, RUN, FOLD);
  type ctrl_t is record
    state : state_t;
    n     : unsigned(7 downto 0);
    en    : std_logic;
  end record;
  constant CTRL_INIT : ctrl_t := (state => IDLE, n => (others => '0'), en => '0');

  signal ctrl  : ctrl_t := CTRL_INIT;
  signal rnd   : std_logic_vector(31 downto 0);
  signal crc   : std_logic_vector(31 downto 0) := (others => '1');
  signal acc   : unsigned(15 downto 0) := (others => '0');
  signal prod  : unsigned(31 downto 0) := (others => '0');
  signal fold4 : std_logic_vector(3 downto 0) := (others => '0');
begin
  u_prbs : prbs32 port map (clk => clk, en => ctrl.en, q => rnd);

  fsm : process (clk)
  begin
    if rising_edge(clk) then
      case ctrl.state is
        when IDLE => ctrl <= (state => LOAD, n => (others => '0'), en => '0');
        when LOAD => ctrl <= (state => RUN, n => (others => '0'), en => '1');
        when RUN =>
          ctrl.n <= ctrl.n + 1;
          if ctrl.n = 199 then
            ctrl.state <= FOLD;
            ctrl.en <= '0';
          end if;
        when FOLD => ctrl.state <= LOAD;
      end case;
    end if;
  end process;

  datapath : process (clk)
  begin
    if rising_edge(clk) then
      if ctrl.en = '1' then
        crc  <= work.crc_pkg.crc32_byte(crc, rnd(7 downto 0));
        acc  <= acc + unsigned(rnd(15 downto 0));
        prod <= unsigned(rnd(31 downto 16)) * acc;
      end if;
      if ctrl.state = FOLD then
        fold4 <= work.crc_pkg.xor_fold4(crc xor std_logic_vector(prod));
      end if;
    end if;
  end process;

  led <= fold4;
end architecture;
