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
    signal a: std_logic;
    signal a: std_logic;
    signal a: std_logic;
BEGIN
    p1: process(a,b,c) is
    variable a: i32;
    variable b: i32;
    begin
        a <= (a and b);
        a := 12;
        wait; 
        a <= (a and b);
        report "something" severity error;
        wait;
        a <= (a and b);
        report "something" severity error;
    end;
END;