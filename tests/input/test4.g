# gaplint: disable=all, M001, remove-comments
                        for gen in gens do
                            img := pt^gen;
                            if orbnums[img] = -1 then
                                orbnums[img] := num;
                                Add(q,img);
                                if img < rep then
                                    rep := img;
                                fi;
                            fi;
                        od;
                    od;
                    orbmins[num] := rep;
