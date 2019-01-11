// 
var runningDatasets = []

$(".dataset-id").each(function() {
    let $this = $(this);
    let dsid = $this.val();
    console.log(dsid);

});


async function checkerRunning(ds_id) {
    try {
        $.ajax({
            async: true,
            dataType: "json",
            url: '/checkerrunning?dsid='+ds_id,
            data: null,
            success: function(result) {
                return result.running;
            }
        });
    } catch(e) {
        console.log(2);
        throw(e);
    }

}


// Check each dataset
console.log(runningDatasets);