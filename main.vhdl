ENTITY HalfAdder IS
    PORT (
          a: IN std_logic;
          b: IN std_logic;
          s: OUT std_logic;
          c: OUT std_logic
    );
END entity HalfAdder;

-- Mango man

ENTITY HAlfAdder IS

END HalfAdder;

ARCHITECTURE addArchitecture1 of HalfAdder IS
    signal d: std_logic <= 'H';
    signal e: std_logic;
    signal f: std_logic <= (a or d);
    signal g: integer;
BEGIN
    d <= (a or 'H');
    d <= (a or g);
    d <= (a or e);
    a <= (a or e);
    
    p1: process(d,e,f) is
    variable ad: std_logic := 'H';
    variable bd: std_logic := 'H';
    begin
        c <= ((a and bd) or (a and b));
        -- a := 12;
        -- wait; 
        -- a <= (a and b);
        -- report "something" severity error;
        -- wait;
        a <= (a and b);
        report "something" severity error;
    end;
END;