// Journal/Genus hide/show appropriate input
$(() => {
    showJournal();
    showGenus();
    $("#journalSelect").change(() => {
        showJournal();
    });
    $("#genusSelect").change(() => {
        showGenus();
    });
});


// Journal auto-complete
$(function() {
    $(".altJournal").autocomplete({
        source: (request, response) => {
            $.getJSON("/_search_journal", {
                search: request.term
            }, (data) => {
                response(data.results);
            });
        },
        minLength: 2,
    });
});

// Genus auto-complete
$(function() {
    $(".altGenus").autocomplete({
        source: (request, response) => {
            $.getJSON("/_search_genus", {
                search: request.term,
                type: $("#genus_type").children("option:selected").val()
            }, (data) => {
                response(data.results);
            });
        },
        minLength: 2,
    });
});

function showJournal() {
    selected = $("#journalSelect").children("option:selected").val();
    if (selected === "alt") {
        $(".newJournal").hide();
        $(".altJournal").show();
    } else if (selected ==="new") {
        $(".newJournal").show();
        $(".altJournal").hide();
    }
}

function showGenus() {
    selected = $("#genusSelect").children("option:selected").val();
    if (selected === "alt") {
        $(".newGenus").hide();
        $(".altGenus").show();
    } else if (selected ==="new") {
        $(".newGenus").show();
        $(".altGenus").hide();
    }
}