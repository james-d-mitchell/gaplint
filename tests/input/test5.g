#! @BeginGroup XTranslation
#! @GroupTitle XTranslation
#! @Returns a left or right translation
#! @Arguments T, x[, y]
#! @Description
#! For the semigroup <A>T</A> of left or right translations of a semigroup <M>
#! S</M> and <A>x</A> one of:
#! * a mapping on the underlying semigroup; note that in this case only the
#!   values of the mapping on the <Ref Attr="UnderlyingRepresentatives"/> of
#!   <A>T</A> are checked and used, so mappings which do not define translations
#!   can be used to create translations if they are valid on that subset of S;
#! * a list of indices representing the images of the
#!   <Ref Attr="UnderlyingRepresentatives"/> of <A>T</A>, where the ordering
#!   is that of <Ref Oper="PositionCanonical"/> on <A>S</A>;
#! * (for `LeftTranslation`) a list of length `Length(Rows(S))`
#!   containing elements of `UnderlyingSemigroup(S)`; in this case
#!   <A>S</A> must be a normalised Rees matrix semigroup and `y` must be
#!   a Transformation of `Rows(S)`;
#! * (for `RightTranslation`) a list of length `Length(Columns(S))`
#!   containing elements of `UnderlyingSemigroup(S)`; in this case
#!   <A>S</A> must be a normalised Rees matrix semigroup and `y` must be
#!   a Transformation of `Columns(S)`;
#! `LeftTranslation` and `RightTranslation` return the corresponding
#! translations.
#! @BeginExampleSession
#! gap> S := RectangularBand(3, 4);;
#! gap> L := LeftTranslations(S);;
#! gap> s := AsList(S)[1];;
#! gap> f := function(x)
#! > return s * x;
#! > end;;
#! gap> map := MappingByFunction(S, S, f);;
#! gap> l := LeftTranslation(L, map);
#! <left translation on <regular transformation semigroup of size 12, 
#!  degree 8 with 4 generators>>
#! gap> s ^ l;
#! Transformation( [ 1, 2, 1, 1, 5, 5, 5, 5 ] )
#! @EndExampleSession
DeclareOperation("LeftTranslation",
                 [IsLeftTranslationsSemigroup, IsGeneralMapping]);
DeclareOperation("RightTranslation",
                 [IsRightTranslationsSemigroup, IsGeneralMapping]);
#! @EndGroup
