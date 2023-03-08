ENTITY HalfAdder IS
END entity HalfAdder;

ARCHITECTURE addArchitecture1 of HalfAdder IS
    signal s_a: std_logic;
    signal s_b: std_logic;
    signal s: std_logic;
    signal c: std_logic;
BEGIN
    s <= (s_a xor s_b);
    c <= (s_a and s_b);
    
    p1: process is
    begin

	s_a <= 'H';
        s_b <= 'H'; wait for 100 ns;
        s_b <= 'L'; wait for 100 ns;
        s_b <= 'X'; wait for 100 ns;
        s_b <= 'Z'; wait for 100 ns;
        s_b <= 'W'; wait for 100 ns;
        s_b <= 'U'; wait for 100 ns;
        s_b <= '-'; wait for 100 ns;

		s_a <= 'L';
        s_b <= 'H'; wait for 100 ns;
        s_b <= 'L'; wait for 100 ns;
        s_b <= 'X'; wait for 100 ns;
        s_b <= 'Z'; wait for 100 ns;
        s_b <= 'W'; wait for 100 ns;
        s_b <= 'U'; wait for 100 ns;
        s_b <= '-'; wait for 100 ns;

		s_a <= 'X';
        s_b <= 'H'; wait for 100 ns;
        s_b <= 'L'; wait for 100 ns;
        s_b <= 'X'; wait for 100 ns;
        s_b <= 'Z'; wait for 100 ns;
        s_b <= 'W'; wait for 100 ns;
        s_b <= 'U'; wait for 100 ns;
        s_b <= '-'; wait for 100 ns;

		s_a <= 'Z';
        s_b <= 'H'; wait for 100 ns;
        s_b <= 'L'; wait for 100 ns;
        s_b <= 'X'; wait for 100 ns;
        s_b <= 'Z'; wait for 100 ns;
        s_b <= 'W'; wait for 100 ns;
        s_b <= 'U'; wait for 100 ns;
        s_b <= '-'; wait for 100 ns;

		s_a <= 'W';
        s_b <= 'H'; wait for 100 ns;
        s_b <= 'L'; wait for 100 ns;
        s_b <= 'X'; wait for 100 ns;
        s_b <= 'Z'; wait for 100 ns;
        s_b <= 'W'; wait for 100 ns;
        s_b <= 'U'; wait for 100 ns;
        s_b <= '-'; wait for 100 ns;

		s_a <= 'U';
		s_b <= 'H'; wait for 100 ns;
		s_b <= 'L'; wait for 100 ns;
		s_b <= 'X'; wait for 100 ns;
		s_b <= 'Z'; wait for 100 ns;
		s_b <= 'W'; wait for 100 ns;
		s_b <= 'U'; wait for 100 ns;
		s_b <= '-'; wait for 100 ns;

		s_a <= '-';
        s_b <= 'H'; wait for 100 ns;
        s_b <= 'L'; wait for 100 ns;
        s_b <= 'X'; wait for 100 ns;
        s_b <= 'Z'; wait for 100 ns;
        s_b <= 'W'; wait for 100 ns;
        s_b <= 'U'; wait for 100 ns;
        s_b <= '-'; wait for 100 ns;	
    end;
END;