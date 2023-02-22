ENTITY HalfAdder IS
    PORT (
          a: IN std_logic;
          b: IN std_logic;
          s: OUT std_logic;
          c: OUT std_logic
    );
END HalfAdder;

ARCHITECTURE addArchitecture1 of HalfAdder IS
BEGIN
    s <= a;
    c <= x"0110a1af01";
    s <= ((a or b) and c);
END;