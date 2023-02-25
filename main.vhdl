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
    p1: process(d,e,f) is
    variable ad: std_logic := 'H';
    begin
        -- ad := ((a  and bd) or (a and b));
        -- a := 'L';
        -- wait; 
        -- a <= (a and b);
        -- report "something" severity error;
        -- wait;
        -- s <= (ad and b);
        if a then
            s <= (a xor b);
        elsif a then
            s <= (a or b);
        else
            s <= a;
        end if;
        -- report "something" severity error;
    end;
END;