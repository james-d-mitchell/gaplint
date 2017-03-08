1 + 1+ 1; # 1 warning
1 + 1;    # 0 warnings
1- 1; foo := x -> x ^ 2; # 1 warning
# duplicate-free # 0 warnings
x := "duplicate-free"; # 0 warnings
x := "askjdaskjd"+"aksjdalskjd"; # 1 warning
x := "#";  # 0 warnings
x ^ -1;  # 0 warnings
x ^ - 1; # Should give a warning but doesn't
x := "\"dasjlkdjsa\""; # 0 warnings
x^ 90 # 1 warning
if x <>3 then# 1 warning
fi;
[1..10] # 1 warning 
function(arg...) # 0 warnings
end;
x :=  3;
x:= 1;


[ 1 .. 2]; # 1 warning
[,,, 1]; # 0 warnings
### A comment with too many hashes
""" A multiline string in a single line. x^-1"""
""" A multiline string in  1-2
several lines.
Another line. Something that should generate a warning is 1-2"""
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
if x = 1 then 
Print("testing inappropriate indentation");
fi;
