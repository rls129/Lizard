ENTITY HalfAdder IS
    PORT (
          a: IN std_logic;
          b: OUT std_logic
    );
END entity HalfAdder;

-- Mango man

-- ENTITY HAlfAdder IS

-- END HalfAdder;

ARCHITECTURE addArchitecture1 of HalfAdder IS
    signal a: std_logic;
BEGIN
    -- b <= (a xor a);
    p1: process is
    variable ad: std_logic := 'H';
    begin
        -- ad := ((a  and bd) or (a and b));
        -- a := 'L';
        -- wait; 
        -- a <= (a and b);
        -- report "something" severity error;
        -- wait;
        -- s <= (ad and b);
        wait for 1 ns;
        while (g /= '1') loop
            if (b = 'u') then
                b <= '0';
                wait for 1 ns;
            elsif (b = '0') then
                b <= '1';
                wait for 1 ns;
            else
                g <= '1';
                wait for 1 ns;
            end if;
        end loop;
        g <= '1';
        wait for 10 ns;
        -- report "something" severity error;
    end;
END;