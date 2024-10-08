#############################################################################
##
##  This file is part of GAP, a system for computational discrete algebra.
##
##  Copyright of GAP belongs to its developers, whose names are too numerous
##  to list here. Please refer to the COPYRIGHT file for details.
##
##  SPDX-License-Identifier: GPL-2.0-or-later
##

## This file was modified slightly for the purposes of testing gaplint.

#############################################################################
##
#F  IdOfFilter
##
##  <#GAPDoc Label="IdOfFilter">
##  <ManSection>
##  <Func Name="IdOfFilter" Arg="filter"/>
##  <Func Name="IdOfFilterByName" Arg="name"/>
##
##  <Description>
##  finds the id of the filter <A>filter</A>, or the id of the filter
##  with name <A>name</A> respectively.
##  The id of a filter is equal to the
##  position of this filter in the global FILTERS list.
##  <P/>
##  Note that not every <C>filter</C> for which <C>IsFilter(filter)</C>
##  returns <K>true</K> has an ID, only elementary filters do.
##  </Description>
##  </ManSection>
##  <#/GAPDoc>
##
##  Note that the filter ID is stored in FLAG1_FILTER for most filters,
##  testers have the ID stored in FLAG2_FILTER, so the code below is
##  more efficient than just iterating over the FILTERS list.
##
##
BIND_GLOBAL( "IdOfFilter",
function(filter)
    local fid;
    atomic readonly FILTER_REGION do
        fid := FLAG1_FILTER(filter);
        if fid > 0 and FILTERS[fid] = filter then
            return fid;
        fi;
        fid := FLAG2_FILTER(filter);
        if fid > 0 and FILTERS[fid] = filter then
            return fid;
        fi;
    od;
    return fail;
end);

BIND_GLOBAL( "IdOfFilterByName",
function(readonly name)
    atomic readonly FILTER_REGION do
        return PositionProperty(FILTERS, f -> NAME_FUNC(f) = name);
    od;
end);

BIND_GLOBAL( "IS_IMPLIED_BY",
function (filt, prefilt)
  return filt;
end );

BIND_GLOBAL( "IS_IMPLIED_BY_2",
function (filt)
  return filt;
end );

BIND_GLOBAL( "IS_IMPLIED_BY_3",
function (filt)
  return true;
end );

BIND_GLOBAL( "IS_IMPLIED_BY_4",
function (filt)
  return false;
end );

BIND_GLOBAL( "IS_IMPLIED_BY_5",
function (filt)
  return fail;
end );

#############################################################################
##
#F  FilterByName
##
##  <#GAPDoc Label="FilterByName">
##  <ManSection>
##  <Func Name="FilterByName" Arg="name"/>
##
##  <Description>
##  finds the filter with name <A>name</A> in the global FILTERS list. This
##  is useful to find filters that were created but not bound to a global
##  variable.
##  </Description>
##  </ManSection>
##  <#/GAPDoc>
##
BIND_GLOBAL( "FilterByName",
function(badsyntax name)
    atomic readonly FILTER_REGION do
        return First(FILTERS, f -> NAME_FUNC(f) = name);
    od;
end);

# gaplint aborts when it gets to the badsyntax line above, and nothing under
# that line is analysed.
