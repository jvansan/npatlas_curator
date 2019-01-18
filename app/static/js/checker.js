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
    var runningDatasets = {};
    var completeDatasets = [];
    for (var idx of datasetIds) {
        const result = await checkDatasetRunning(idx);
        if (result.running === true) {
            runningDatasets[idx] = result.task_id;
        } else if (result.complete === true) {
            completeDatasets.push(idx);
        }
    }
    return [runningDatasets, completeDatasets];
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
                        </div>
                    </div><br>`);
    newRow.progressbar();
    newRow.insertAfter(infoRow);
}

function completeDataset(datasetId) {
    // Remove status data
    let infoRow = $(`#dataset-${datasetId}-info-row`);
    let statusRow = $(`#dataset-${datasetId}-status-row`);
    statusRow.next().remove();
    statusRow.remove();
    // add new stuff
    let newRow = $(`
    <div class="row" id=dataset-${datasetId}-complete-status>
        <div class="col-lg-12 text-center">
            Dataset complete running!
        </div>
    </div>
    `);
    newRow.insertAfter(infoRow);
    // Fix button
    $(`#dataset-checker-button-${datasetId}`).text("Run Checker").removeAttr("disabled");
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
 
async function launchMonitoring(datasetId, taskId) {
    // Monitor status
    updateProgress(datasetId, taskId);
}

async function updateProgress(datasetId, taskId) {
    const statusUrl = '/checkerstatus?taskid='+taskId;    
    try {
        result = await $.getJSON(statusUrl);
    } catch(err) {
        // console.log(err);
        throw "Error, could not get status for Dataset "+ datasetId;
    }

    if (result.state == 'SUCCESS') {
        completeDataset(datasetId);
    } else if (result.state == 'FAILURE') {
        failedDataset(datasetId);
    } else {
        progress = parseInt(result.current * 100 / result.total);
        $(`#dataset-${datasetId}-progress-bar`).progressbar({"value": progress});
        $(`#dataset-${datasetId}-progress`).text(`${progress} %`);
        $(`#dataset-${datasetId}-status`).text(`${result.state} : ${progress} %`);
        
        if (progress < 100) {
            await timeout(2000);
            updateProgress(datasetId, taskId);
        }
    }
    

}

function startChecker(datasetId) {
    
    // if dataset already running
    if ($(`#dataset-${datasetId}-completed`)[0].childNodes[1].classList[1] !== "fa-check-circle" ) {
        throw "Dataset hasn't been completed!";
    }
    // Remove complete status if re-running
    $(`#dataset-${datasetId}-complete-status`).remove();

    $.post(`/checkerstart/dataset${datasetId}`, {})
        .done( function(retJson) {
            initRunningProgress(datasetId);
            updateProgress(datasetId, retJson.task_id);
        }).fail( () => {
            alert('Failed to start checker for dataset '+datasetId);
        });
}

// First get all the dataset IDs on the page
// Next check if they are running and get the Celery Task ID if so
//  -> Store these results in a JSON
// Finally display results and start monitoring of running tasks
async function main() {
    try {
        var datasetIds = await collectDatasetIds();
        console.log('Datasets ids: [' + datasetIds.join(', ') + ']');
        var [runningDatasets, completeDatasets] = await getRunningDatasets(datasetIds);
        console.log('Running Datasets: [' + Object.keys(runningDatasets).join(', ') + ']');
        console.log('Complete Datasets: [' + Object.keys(completeDatasets).join(', ') + ']');

        for (var idw of completeDatasets) {
            completeDataset(idw);
        }

        for (var idx of Object.keys(runningDatasets)) {
            initRunningProgress(idx);
        }
        // Run monitoring of datasets
        for (var idy of Object.keys(runningDatasets)) {
            let taskId = runningDatasets[idy];
            launchMonitoring(idy, taskId);
        }
    } catch(err) {
        console.log(err);
    }   
}

main();