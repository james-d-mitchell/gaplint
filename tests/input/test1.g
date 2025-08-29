# gaplint: disable=a-rule, another-rule
# gaplint: disable=another-rule2, M000
1 + 1+ 1; # 1 warning
1 + 1;    # 0 warnings
1- 1; foo := x -> x ^ 2; # 1 warning
# duplicate-free # 0 warnings
x := "duplicate-free"; # 0 warnings
# gaplint: disable(nextline)=bananas, whitespace-op-plus
x := "askjdaskjd"+"aksjdalskjd"; # 1 warning
x := "#";  # 0 warnings
x ^ -1;  # 0 warnings #gaplint: disable=bananas
x ^ - 1; # 1 warning
x := "\"dasjlkdjsa\""; # 0 warnings
x^ 90 # 1 warning
if x <>3 then# 1 warning
fi;
[1..10] # 1 warning 
function(arg...) # 0 warnings
  return - 1; # 1 warning
end;
return -1 * [1 .. 2]; # 0 warning
return - 1 * [1 .. 2]; # 1 warning
return [1 .. 2] * -1; # 0 warning
return [1 .. 2] * - 1; # 1 warning
x :=  3;
x:= 1;
x   := 1;


[ 1 .. 2]; # 1 warning
[,,, 1]; # 0 warnings
### A comment with too many hashes
""" A multiline string in a single line. x^-1"""
""" A multiline string in  1-2
several lines.
Another line. Something that should generate a warning is 1-2"""
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
if x = 1 then 
Print("testing inappropriate indentation");
fi;
"A string containing escaped backslashes right at the end \\";
"A string \\containing escaped \"backslashes\" right at the end \\\\";
foo := function(x, y, z) local t; return x + y + z; end;
foo := function(x, y, localt, 1a1a, 1b)
end;
#foo := function(x, x) end;
foo := function(x, y, z)
  local t;
  return x + y + z;
end;
#foo := function(x, y, x)
#  local t;
#  return x + y + z;
#end;
#foo := function(x, y, z)
#  local a, b, c, z;
#  return x + y + z;
#end;
foo := function(x, y, z)
  return x + y;
end;
function(x)
  local test, y;
  y := 0;
  test := rec(x := y, y := x, z := (1,2,3));
end;
foo := function(x, y, z)
  Print("test");
  return x + y + z;
end;
# 50 warnings
x := 0;;  # gaplint: disable=W014
