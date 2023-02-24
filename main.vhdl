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
BEGIN
    p1: process(d,e,f) is
    variable a: std_logic := 'H';
    variable b: std_logic := 'H';
    begin
        a <= (a and b);
        a := 12;
        wait; 
        a <= (a and b);
        report "something" severity error;
        wait;
        a <= (a and b"010101");
        report "something" severity error;
    end;
END;