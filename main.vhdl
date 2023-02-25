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
    signal g: integer;
BEGIN
    -- b <= (a xor a);
    p1: process(a, b) is
    variable ad: std_logic := 'H';
    begin
        -- ad := ((a  and bd) or (a and b));
        -- a := 'L';
        -- wait; 
        -- a <= (a and b);
        -- report "something" severity error;
        -- wait;
        -- s <= (ad and b);
        if (a = a) then
            b <= (a xor a);
        elsif (g = '0') then
            g <= (g and '0');
        else
            b <= a;
        end if;
        -- report "something" severity error;
    end;
END;