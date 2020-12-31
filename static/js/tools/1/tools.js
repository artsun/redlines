window.saveWrapper = function saveWrapper(){
	let output = new Array();
	for (let editor of EDITORS) {
	editor.save().then((outputData) => {
  output.push(outputData);
}).catch((error) => {
  console.log('Saving failed: ', error)
});
}
download(output);
}


function download(content) {
	content = JSON.stringify(content);
	console.log('Saving : ', content);
    var a = document.createElement("a");
    var file = new Blob([content], {type: 'text/plain'});
    a.href = URL.createObjectURL(file);
    a.download = 'ResultDoc.txt';
    a.click();
}
