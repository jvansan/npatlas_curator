function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function collectDatasetIds() {
    let datasetIds = [];
    $(".dataset-id").each(function() {
        let dsid = $(this).val();
        datasetIds.push(dsid);
    });
    return datasetIds;
}

async function checkDatasetRunning(datasetId) {
    let result = await $.getJSON(`/checkerrunning?dsid=${datasetId}`);
    return result;
}

async function getRunningDatasets(datasetIds) {
    var standardDatasets = {};
    var runningDatasets = {};
    var completeDatasets = [];
    for (var idx of datasetIds) {
        const result = await checkDatasetRunning(idx);
        if (result.standard === true) {
            standardDatasets[idx] = result.task_id;
        } else if (result.running === true) {
            runningDatasets[idx] = result.task_id;
        } else if (result.complete === true) {
            completeDatasets.push(idx);
        }
    }
    return [standardDatasets, runningDatasets, completeDatasets];
}


async function monitorStandardization(datasetId, taskId) {
    const statusUrl = `/standardstatus?taskid=${taskId}`;
    $(`#dataset-checker-button-${datasetId}`).attr("disabled", "disabled").html("Standardization Running");
    try {
        result = await $.getJSON(statusUrl);
    } catch(err) {
        // console.log(err);
        throw "Error, could not get standardization status for Dataset "+ datasetId;
    }

    if (result.state === "SUCCESS") {
        $(`#dataset-checker-button-${datasetId}`).removeAttr("disabled").html("Run Checker")
            .attr("onclick", `startChecker(${datasetId})`);

        markComplete(`#dataset-${datasetId}-completed`);
    } else if (result.state === "FAILURE") {
        alert("Failed to standardize dataset!");
        $(`#dataset-checker-button-${datasetId}`).removeAttr("disabled").html("Run Standardization");
    } else {
        await timeout(3000);
        monitorStandardization(datasetId, taskId);
    }

}


function initRunningProgress(datasetId) {
    // Disable button
    $(`#dataset-checker-button-${datasetId}`).attr("disabled", "disabled").html('Checker Running');
    // Setup progress data
    let infoRow = $(`#dataset-${datasetId}-info-row`);
    let newRow = $(`<div class="row col-lg-12" id="dataset-${datasetId}-status-row">
                        <div class="row col-lg-12">
                            <div class="progress-bar col-lg-12" id="dataset-${datasetId}-progress-bar">
                                <div class="progress-label" id="dataset-${datasetId}-progress">
                                    0 %
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row" style="border: none;">
                        <div class="col-lg-12 text-center" id="dataset-${datasetId}-status">
                            ...
                        </div><br>
                    </div>`);
    newRow.progressbar();
    newRow.insertAfter(infoRow);
}

function completeDataset(datasetId, resolveUrl) {
    // Remove status data
    let infoRow = $(`#dataset-${datasetId}-info-row`);
    let statusRow = $(`#dataset-${datasetId}-status-row`);
    statusRow.next().remove();
    statusRow.remove();
    // add new stuff
    let newRow = $(`
    <div class="row" id=dataset-${datasetId}-complete-status>
        <div class="col-lg-12 text-center">
            Checker complete running for dataset!
            <br>
            <a class="btn btn-success" href="${resolveUrl}" style="display:inline-block;padding-button:12px">
                Resolve Problems and Insert Data
            </a>
        </div>
    </div>
    `);
    newRow.insertAfter(infoRow);
    // Fix button
    $(`#dataset-checker-button-${datasetId}`).text("Run Checker").removeAttr("disabled");
    markComplete(`#dataset-${datasetId}-checked`);
}

function failedDataset(datasetId) {
    let infoRow = $(`#dataset-${datasetId}-info-row`);
    let statusRow = $(`#dataset-${datasetId}-status-row`);
    statusRow.next().remove();
    statusRow.remove();
    let newRow = $(`
    <div class="row">
        <div class="col-lg-12 text-center">
            Dataset failed... Please dig into this admin!
        </div>
    </div>`);
    newRow.insertAfter(infoRow);
}
 

async function monitorChecker(datasetId, taskId) {
    const statusUrl = '/checkerstatus?taskid='+taskId;    
    try {
        result = await $.getJSON(statusUrl);
    } catch(err) {
        // console.log(err);
        throw "Error, could not get Checker status for Dataset "+ datasetId;
    }

    if (result.state == 'SUCCESS') {
        resolveUrl = result.result;
        completeDataset(datasetId, resolveUrl);
    } else if (result.state == 'FAILURE') {
        $(`#dataset-checker-button-${datasetId}`).removeAttr("disabled");
        failedDataset(datasetId);
    } else {
        progress = parseInt(result.current * 100 / result.total);
        $(`#dataset-${datasetId}-progress-bar`).progressbar({"value": progress});
        $(`#dataset-${datasetId}-progress`).text(`${progress} %`);
        $(`#dataset-${datasetId}-status`).text(`${result.state} : ${progress} %`);
        
        if (progress < 100) {
            await timeout(2000);
            monitorChecker(datasetId, taskId);
        }
    }
}

function startChecker(datasetId) {
    
    // if dataset already running
    if ($(`#dataset-${datasetId}-completed`)[0].childNodes[1].classList[1] !== "fa-check-circle" ) {
        throw "Dataset hasn't been completed!";
    }
    // Remove complete status if re-running
    startUrl = `/checkerstart/dataset${datasetId}`;
    if ($(`#dataset-${datasetId}-checked`).children('i').attr('class').split(/\s+/).includes("fa-check-circle")) {
        if (confirm('Re-run checker? Cancel will run checker de novo.')) {
            startUrl = `/checkerstart/dataset${datasetId}?restart=true`;
        }
    }
    $(`#dataset-${datasetId}-complete-status`).remove();
    markIncomplete(`#dataset-${datasetId}-checked`);

    $.post(startUrl, {})
        .done( function(retJson) {
            initRunningProgress(datasetId);
            monitorChecker(datasetId, retJson.task_id);
        }).fail( () => {
            alert('Failed to start checker for dataset '+datasetId);
        });
}

function startStandardization(datasetId) {
    $.post(`/standardize/dataset${datasetId}`, {})
        .done( () => {
            monitorStandardization(datasetId, retJson.task_id);
        }).fail( () => {
            alert('Failed to start standardization for dataset '+datasetId);
        });
}


function markComplete(idString) {
    let statusObject = $(idString).children("i");
    statusObject.removeClass("fa-times-circle").removeClass("red");
    statusObject.removeClass("fa-clock").removeClass("yellow");
    statusObject.addClass("fa-check-circle").addClass("green");
}

function markIncomplete(idString) {
    let statusObject = $(idString).children("i");
    statusObject.removeClass("fa-check-circle").removeClass("green");
    statusObject.addClass("fa-times-circle").addClass("red");
}

// First get all the dataset IDs on the page
// Next check if they are running and get the Celery Task ID if so
//  -> Store these results in a JSON
// Finally display results and start monitoring of running tasks
async function main() {
    try {
        var datasetIds = await collectDatasetIds();
        console.log('Datasets ids: [' + datasetIds.join(', ') + ']');
        var [standardDatasets, runningDatasets, completeDatasets] = await getRunningDatasets(datasetIds);
        console.log('Standardizing Datasets: [' + Object.keys(standardDatasets).join(', ') + ']');
        console.log('Running Datasets: [' + Object.keys(runningDatasets).join(', ') + ']');
        console.log('Complete Datasets: [' + completeDatasets.join(', ') + ']');

        for (var idv of completeDatasets) {
            let resolveUrl = `/admin/resolve/dataset${idv}`;
            completeDataset(idv, resolveUrl);
        }

        for (var idw of Object.keys(standardDatasets)) {
            let taskId = standardDatasets[idw];
            monitorStandardization(idw, taskId);
        }

        // Run monitoring of datasets
        for (var idx of Object.keys(runningDatasets)) {
            initRunningProgress(idx);
            let taskId = runningDatasets[idx];
            monitorChecker(idx, taskId);
        }
    } catch(err) {
        console.log(err);
    }   
}

main();