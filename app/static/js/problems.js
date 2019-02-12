function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function insertionComplete(datasetId) {
    // Temporary function
    alert("Dataset "+datasetId+" complete!");
    let finish = $(`
    <div class="text-center">
        <h4>Dataset has been inserted!</h4>
        <a href="/admin/datasets">Go Back!</a>
    </div>`);
    finish.insertAfter($(`#dataset-insert-button`).parent());
}


async function monitorInsertion(datasetId, taskId) {
    const statusUrl = `/insertstatus?taskid=${taskId}`;
    $(`#dataset-insert-button`).attr("disabled", "disabled");
    try {
        result = await $.getJSON(statusUrl);
    } catch(err) {
        throw "Error, could not insert Dataset "+datasetId;
    }

    if (result.state === "SUCCESS") {
        insertionComplete(datasetId);
    } else if (result.state === "FAILURE") {
        alert('Failed to insert dataset!');
        $(`#dataset-insert-button`).removeAttr("disabled");
    } else {
        await timeout(3000);
        monitorInsertion(datasetId, taskId);
    }
}


function startInserter(datasetId) {
    $.post('/insert/dataset'+datasetId, {})
        .done( (retJson) => {
            monitorInsertion(datasetId, retJson.task_id);
        }).fail( () => {
            alert('Failed to insert Dataset '+ datasetId);
        });
}
