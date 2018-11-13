$(document).ready(() => {

    // For page to reload when the back button was used
    window.addEventListener( "pageshow", function ( event ) {
        var historyTraversal = event.persisted ||
                               ( typeof window.performance != "undefined" &&
                                    window.performance.navigation.type === 2 );
        if ( historyTraversal ) {
          // Handle page restore.
          window.location=window.location;
        }
      });

    // variables
    const regex = /^10.\d{4,9}\//g;
    var currentPath = window.location.pathname

    // Initialize SmilesDrawer
    var options = {
        width: 400,
        height: 400
    }
    var smilesDrawer = new SmilesDrawer.Drawer(options);

    // Show all alerts except the one which arises when you add a new compound
    $(".alert").each(function(idx) {
        if (!$(this).text().includes("Error in the Compounds field - {'name': ")) {
            $(this).show();
        }
    })

    // Draw compounds on page load
    $(".smiles-input").each( function(idx) {
        let $this = $(this);
        let smiles = $this.val().trim()
        console.log(idx + " " + smiles);
        let $canvas = $("#compound-canvas-"+idx)
        $canvas.attr("alt", smiles);
        // $canvas.next().html()
        // Parse and draw compound
        SmilesDrawer.parse(smiles, function(tree) {
            // console.log(tree);
            smilesDrawer.draw(tree, "compound-canvas-" + idx, "light", false);
            $canvas.next().text(smilesDrawer.getMolecularFormula());
        }, function(err) {
            console.log(err);
        });
    });

    // Add tab buttons and menu items for each compound
    $(".compound-row").each( function() {
        let $this = $(this);
        let rowNum = parseInt($this.attr("id").split("-")[2]);
        let compoundName = $this.find("#compounds-"+rowNum+"-name").val();
        let compoundKnown = $this.find("#compounds-"+rowNum+"-npaid").val();
        if (compoundName.length == 0) {
            compoundName = "Name";
        }
        var btnType;
        if (compoundKnown){
            btnType = 'btn-success';
        } else {
            btnType = 'btn-warning';
        }

        // Buttons
        let btnString = "<button class='compound-tab btn "+btnType+"' id='compound-tab-"+rowNum+"' type=button>";
        btnString = btnString + compoundName + "</button>";
        $("#tabDiv").append(btnString);

        // Menu Items
        let menuItemString = "<li role='presentation'><button class='compound-menu' role='menuitem' id='compound-menu-"+rowNum+"' type=button>";
        menuItemString = menuItemString + compoundName + "</a></li>";
        $("#compoundMenu").append(menuItemString);
    })

    // Show correct # of compounds on menu
    updateMenuCount()

    // Hide all but first for compound field unless just added new compound
    // If new compound (catching by error), show that one
    $(".compound-row").hide();
    if ( $("#session-compId").length != 0 ){
        let index = $("#session-compId").val();
        $(".compound-row:eq( {} )".format(index)).show();
        $(".compound-tab:eq( {} )".format(index)).addClass("active");
        $tabDiv = $("#tabDiv")
        $tabDiv.scrollLeft($tabDiv.width()*100)
    } else {
        $(".compound-row").first().show();
        $(".compound-tab").first().addClass("active");
    }

    // Smiles input event
    $(".smiles-input").on("keyup", function() {
        let $this = $(this);
        let smiles = $this.val().trim();
        // console.log(smiles);
        let rowNum = parseInt($this.attr("id").split("-")[1]);
        let $canvas = $("#compound-canvas-"+rowNum)
        $canvas.attr("alt", smiles);
        // console.log(smiles.length);
        if (smiles.length == 0 ){
            $canvas[0].getContext("2d").clearRect(0, 0, $canvas[0].width, $canvas[0].height);
            $canvas.next().text(" ")
        } else {
        // Parse and draw compound
        SmilesDrawer.parse(smiles, function(tree) {
            // console.log(tree);
            smilesDrawer.draw(tree, "compound-canvas-" + rowNum, "light", false);
            $canvas.next().text(smilesDrawer.getMolecularFormula());
        }, function(err) {
            console.log(err);
        });
        }
    });

    // Compound select from tabs
    $(".compound-tab").on("click", function() {
        let rowNum = $(this).attr("id").split("-")[2];
        let $target = $("#compound-row-"+rowNum);
        // Hide all compound rows first then show target
        $(".compound-row").hide();
        $target.show();
        // Scroll tab to center
        scrolltabDiv(rowNum)
        // Make tab appear active
        $(".compound-tab").removeClass("active");
        $(this).addClass("active");
    });

    // Compound select from menu
    $(".compound-menu").on("click", function(e) {
        e.preventDefault()
        let rowNum = $(this).attr("id").split("-")[2];
        let $this = $("#compound-tab-"+rowNum);
        let $target = $("#compound-row-"+rowNum);
        // Hide all compound rows first then show target
        $(".compound-row").hide();
        $target.show();
        // Scroll tab to center
        scrolltabDiv(rowNum)
        // Make tab appear active
        $(".compound-tab").removeClass("active");
        $this.addClass("active");
    })

    // Write Name to Tab after leave input
    $(".name-input").on("blur", function() {
        let rowNum = $(this).attr("id").split("-")[1];
        let $target1 = $("#compound-tab-"+rowNum);
        let $target2 = $("#compound-menu-"+rowNum);
        // console.log($(this).val());
        if ($(this).val().length > 0) {
            $target1.text($(this).val());
            $target2.text($(this).val());
        } else {
            $target1.text("Name");
            $target2.text("Name");
        }
    });

    // Close alert about num compounds if the field gets fixed
    $("#num_compounds").on("keyup", function() {
        if ($(this).val() == $(".compound-tab").length) {
            $('.close').each( function() {
                if ($(this).parent().text().includes("Number of Compounds field")) {
                    $(this).parent().alert("close");
                }
            })
        }
    })

    // DOI Linkout
    if ($("input[id='doi']").val().match(regex)) {
        let link = "https://doi.org/" + $("input[id='doi']").val();
        $("#doi-link").attr("href", link).show();
    }

    // DOI Linkout event
    $("input[id='doi']").on("keyup", function() {
        // console.log($(this));
        let doi = $(this).val();
        // console.log(doi);
        $target = $("#doi-link");
        if (doi.match(regex)) {
            let link = "https://doi.org/" + doi;
            $target.attr("href", link).show();
        } else {
            $target.attr("href", "#").hide();;
        }
    });

    // PMID Linkout
    if (parseInt($("input[id='pmid']").val())) {
        let link = "https://www.ncbi.nlm.nih.gov/pubmed/" + $("input[id='pmid']").val()
        $("#pmid-link").attr("href", link).show();
    }

    // PMID Linkout event
    $("input[id='pmid']").on("keyup", function() {
        // console.log($(this));
        let pmid = $(this).val();
        $target = $("#pmid-link");
        if (parseInt(pmid) > 0) {
            let link = "https://www.ncbi.nlm.nih.gov/pubmed/" + pmid;
            $target.attr("href", link).show();
        } else {
            $target.attr("href", "#").hide();
        }
    });

    // Forward an article
    $("#fwdArticle").on("click", function() {
        $.post('/data/nextArticle', {
            url: currentPath
        }).done( function(retJson) {
            // console.log(retJson['url']);
            if (retJson['url']) {
                window.location.replace(window.location.origin + '/' + retJson['url']);
            } else {
                alert("No next article.")
            }
        }).fail( function() {
            alert("Could not access server. Please contact the admin.")
        });
    });

    // Back an article
    $("#backArticle").on("click", function() {
        $.post('/data/backArticle', {
            url: currentPath
        }).done( function(retJson) {
            // console.log(retJson['url']);
            if (retJson['url']) {
                window.location.replace(window.location.origin + '/' + retJson['url']);
            } else {
                alert("No previous article.")
            }
        }).fail( function() {
            alert("Could not access server. Please contact the admin.")
        });
    });

    // Add a compound
    $("#addCompound").on("click", function() {
        // Need to save article data and send to POST
        let article = {
            pmid: $("#pmid").val(),
            doi: $("#doi").val(),
            title: $("#title").val(),
            journal: $("#journal").val(),
            authors: $("#authors").val(),
            abstract: $("#abstract").val(),
            year: $("#year").val(),
            pages: $("#pages").val(),
            vol: $("#volume").val(),
            iss: $("#issue").val(),
            num_compounds: $("#num_compounds").val(),
            needs_work: $("#needs_work").is(":checked"),
            notes: $("#notes").val()
        }
        let compounds = []
        // Need to collect compound data and send in POST to save data
        $(".compound-row").each(function() {
            let rowNum = parseInt($(this).attr("id").split("-")[2]);
            let compound = {
                id: $("#compounds-{}-id".format(rowNum)).val(),
                name: $("#compounds-{}-name".format(rowNum)).val(),
                smiles: $("#compounds-{}-smiles".format(rowNum)).val(),
                source_organism: $("#compounds-{}-source_organism".format(rowNum)).val(),
                curated_compound: $("#compounds-{}-curated_compound".format(rowNum)).is(":checked")
            };
            compounds.push(compound)
        })
        // Send POST
        $.ajax({
            url: "/data/addCompound",
            type: "POST",
            data: JSON.stringify({url: currentPath, compounds: compounds, article: article}),
            contentType: "application/json; charset=utf-8",
            success: function(retJson) {
                    if (retJson['url']) {
                        window.location.replace(window.location.origin + '/' + retJson['url']);
                    } else {
                        alert("Something else happended...")
                    }
                    window.location=window.location;
                },
            error: function() {
                    alert("Could not access server. Please contact admin.")
                }
        })
    })

    // Remove a compound
    $("#delCompound").on("click", function() {
        // Get current compound id
        $tab = $("button.compound-tab.active");
        let rowNum = $tab.attr("id").split("-")[2];
        let compId = $("#compounds-{}-id".format(rowNum)).val();
        if ($("#compounds-{}-curated_compound".format(rowNum)).is(":checked")) {
            $("#dialog-confirm").removeAttr("style");
            $("#dialog-confirm").dialog({
                resizable: false,
                height: "auto",
                width: 400,
                modal: true,
                buttons: {
                    "Delete Compound": function() {
                        deleteCompound(currentPath, compId);
                        $(this).dialog('close');
                    },
                    Cancel: function() {
                        $(this).dialog('close');
                    }
                }
            })
        } else {
            deleteCompound(currentPath, compId);
        }
    })

// END jQUERY DOC READY
});

String.prototype.format = function () {
    var i = 0, args = arguments;
    return this.replace(/{}/g, function () {
      return typeof args[i] != 'undefined' ? args[i++] : '';
    });
  };

function updateMenuCount() {
    let $this = $("#compoundMenuBtn");
    let n = $(".compound-menu").length;
    $this.text("Curated Compounds ({})".format(n));
}

function scrolltabDiv(rowNum) {
        let $this = $("#compound-tab-"+rowNum)
        // Scroll tab to center
        // Only if not clicking active tab
        if (!($this.hasClass("active"))) {
            var out = $("#tabDiv");
            var tar = $this;
            var x = out.width();
            var y = tar.outerWidth(true);
            var z = tar.index();
            var q = 0;
            var m = out.find('button');
            //Just need to add up the width of all the elements before our target.
            for(var i = 0; i < z; i++){
                q+= $(m[i]).outerWidth(true);
            }
            out.scrollLeft(Math.max(0, q - (x - y)/2));
        }
}

function deleteCompound(currentPath, compId) {
    if ($(".compound-row").length == 1) {
        alert("Cannot delete every compound from an article. Please add a real compound before deleting this one.")
        return
    }
    // Need to save article data and send to POST
    let article = {
        pmid: $("#pmid").val(),
        doi: $("#doi").val(),
        title: $("#title").val(),
        journal: $("#journal").val(),
        authors: $("#authors").val(),
        abstract: $("#abstract").val(),
        year: $("#year").val(),
        pages: $("#pages").val(),
        vol: $("#volume").val(),
        iss: $("#issue").val(),
        num_compounds: $("#num_compounds").val(),
        needs_work: $("#needs_work").is(":checked"),
        notes: $("#notes").val()
    }
    let compounds = []
    // Need to collect compound data and send in POST to save data
    $(".compound-row").each(function() {
        let rowNum = parseInt($(this).attr("id").split("-")[2]);
        let compound = {
            id: $("#compounds-{}-id".format(rowNum)).val(),
            name: $("#compounds-{}-name".format(rowNum)).val(),
            smiles: $("#compounds-{}-smiles".format(rowNum)).val(),
            source_organism: $("#compounds-{}-source_organism".format(rowNum)).val(),
            curated_compound: $("#compounds-{}-curated_compound".format(rowNum)).is(":checked")
        };
        compounds.push(compound)
    })
    // Send POST
    $.ajax({
        url: "/data/delCompound",
        type: "POST",
        data: JSON.stringify({url: currentPath, compounds: compounds, article: article, compId: compId}),
        contentType: "application/json; charset=utf-8",
        success: function(retJson) {
                if (retJson['url']) {
                    window.location.replace(window.location.origin + '/' + retJson['url']);
                } else {
                    alert("Something else happended...")
                }
                window.location=window.location;
            },
        error: function() {
                alert("Could not access server. Please contact admin.")
            }
    });
}
