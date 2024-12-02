while pos <= len and irratname[ pos ] in "\'\"" do
  dashes:= dashes + 1;
  if irratname[ pos ] = '\"' or pos = '"' then
    dashes:= dashes + 1;
  fi;
  pos:= pos + 1;
od;
pos2:= pos;
while pos2 <= len and IsDigitChar( irratname[ pos2 ] ) do
  pos2:= pos2+1;
od;
if pos2 = pos and lpos = 8 then
  N:= 1;
else
  N:= Int( irratname{ [ pos .. pos2 - 1 ] } );
fi;
if dashes = 0 then
  qN:= funcs[ lpos ]( N );
else
  qN:= funcs[ lpos ]( N, dashes );
fi;
pos:= pos2;
irrat:= coeff * qN;
if len < pos then
  return irrat;
fi;

# Get the Galois automorphism.
if irratname[ pos ] = '*' then
  pos:= pos + 1;
  if pos <= len and irratname[ pos ] = '*' then
    pos:= pos + 1;
    pos2:= pos;
    while pos2 <= len and IsDigitChar( irratname[ pos2 ] ) do
      pos2:= pos2 + 1;
    od;
    gal:= Int( irratname{ [ pos .. pos2-1 ] } );
    if gal = 0 then
      irrat:= ComplexConjugate( irrat );
    else
      irrat:= GaloisCyc( irrat, -gal );
    fi;
    pos:= pos2;
  elif len < pos or irratname[ pos ] in "+-&" then
    irrat:= StarCyc( irrat );
  else
    pos2:= pos;
    while pos2 <= len and IsDigitChar( irratname[ pos2 ] ) do
      pos2:= pos2 + 1;
    od;
    gal:= Int( irratname{ [ pos .. pos2-1 ] } );
    irrat:= GaloisCyc( irrat, gal );
    pos:= pos2;
  fi;
fi;

while pos <= len do

  # Get ampersand summands.
  if irratname[ pos ] = '&' then
    pos2:= pos + 1;
    while pos2 <= len and IsDigitChar( irratname[ pos2 ] ) do
      pos2:= pos2 + 1;
    od;
    gal:= Int( irratname{ [ pos+1 .. pos2-1 ] } );
    irrat:= irrat + coeff * GaloisCyc( qN, gal );
    pos:= pos2;
  elif irratname[ pos ] in "+-" then
    if irratname[ pos ] = '+' then
      sign:= 1;
      oldpos:= pos+1;
    else
      sign:= -1;
      oldpos:= pos;
    fi;
    pos2:= pos + 1;
    while pos2 <= len and IsDigitChar( irratname[ pos2 ] ) do
      pos2:= pos2 + 1;
    od;
    if pos2 = pos + 1 then
      coeff:= sign;
    else
      coeff:= sign * Int( irratname{ [ pos+1 .. pos2-1 ] } );
    fi;
    pos:= pos2;
    if pos <= len then
      if irratname[ pos ] = '&' then
        pos2:= pos + 1;
        while pos2 <= len and IsDigitChar( irratname[ pos2 ] ) do
          pos2:= pos2 + 1;
        od;
        gal:= Int( irratname{ [ pos+1 .. pos2-1 ] } );
        irrat:= irrat + coeff * GaloisCyc( qN, gal );
        pos:= pos2;
      else
        recurse:= AtlasIrrationality( irratname{ [ oldpos .. len ] } );
        if recurse = fail then
          return fail;
        fi;
        irrat:= irrat + recurse;
        pos:= len+1;
      fi;
    else
      irrat:= irrat + coeff;
    fi;
  else
    return fail;
  fi;
od;
