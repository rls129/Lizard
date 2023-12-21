# Lizard -- Logic Wizard
This is a VHDL simulator made for half year project during 6th semester of computer enginnering of IOE pulchowk.

## How to run
1. Clone the repo and get inside the folder.
  ```sh
  git clone --depth=1 https://github.com/rls129/Lizard/`
  cd Lizard
  ```
2. Create a virtual env and activate it.
  ```sh
  python -m venv .venv
  source .venv/bin/activate # OR
  .venv/bin/Activate.ps1
  ```
3. Install all dependencies from requirements.txt.
  `pip install -r requirements.txt`
4. Run the application
  `python main.py`

## Example Code
```vhdl
entity comparator_1bit is
end entity comparator_1bit;

architecture Behavioral of comparator_1bit is
        signal b_i           :  std_logic;
        signal a_i           :  std_logic;
        signal B_less_A_o    :  std_logic;
begin
    B_less_A_o <= a_i and (b_i nand b_i);

    process is 
    begin
        a_i <= '0';
        b_i <= '0';
        wait for 100 ns;
        a_i <= '0';
        b_i <= '1';
        wait for 100 ns;
        a_i <= '1';
        b_i <= '0';
        wait for 100 ns;
        a_i <= '1';
        b_i <= '1';
        wait for 100 ns;
        wait;
    end process;

end architecture Behavioral;

```

## Outputs

![Screen](https://github.com/rls129/Lizard/assets/88744688/03528f7d-0c03-495c-986d-7408179b75de)
![error](https://github.com/rls129/Lizard/assets/88744688/9529ef4e-53bd-4439-8961-aa27fcf61da7)
![Sucessful](https://github.com/rls129/Lizard/assets/88744688/847c68a1-f6c5-484c-8c99-7d43a0430228)
![output](https://github.com/rls129/Lizard/assets/88744688/cf501b04-e96f-4bc8-886e-b07c9feae9e0)
![network](https://github.com/rls129/Lizard/assets/88744688/1cf97c6f-b40f-4142-b13d-60351da54939)
