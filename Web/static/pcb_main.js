$(function() {
   var dragHandler = function(evt){
      evt.preventDefault();
   };

   var dropHandler = function(evt){
      evt.preventDefault();
      showWaitUpload();
      var files = evt.originalEvent.dataTransfer.files;

      showToastr('success', "Uploading board...");

      var formData = new FormData();
      formData.append("file2upload", files[0]);

      var req = {
         url: "/sendfile",
         method: "post",
         processData: false,
         contentType: false,
         data: formData
      };
      // clean the uploaded file
      uploadedFilePath = undefined;

      var promise = $.ajax(req);
      promise.then(suggestBoardCompletionOnUpload, serverError);
   };

   var dropHandlerSet = {
      dragover: dragHandler,
      drop: dropHandler
   };

   $("#droparea").on(dropHandlerSet);
   $("#suggestControls").hide();
   $("#waitFileUpload").hide();
   //fileUploadSuccess(false); // called to ensure that we have initial data
});

// the latest uploaded file (dragged-and-dropped by the user)
var uploadedFilePath = undefined;
// the latest generated file (received either as a generated or completed file)
var generatedFilePath = undefined;

function changeMode(modeName)
{
   if (modeName == "generate") {
      $("#suggestControls").hide();
      $("#suggestItem").removeClass("selected");
      $("#generateControls").show();
      $("#generateItem").addClass("selected");
   } else {
      $("#suggestControls").show();
      $("#suggestItem").addClass("selected");
      $("#generateControls").hide();
      $("#generateItem").removeClass("selected");
   }
}

function showWaitUpload()
{
   $("#h1Message").hide();
   $("#waitFileUpload").show();
}

function hideWaitUpload()
{
   $("#h1Message").show();
   $("#waitFileUpload").hide();
}

function requestBoardRendering (response){
   file_name = response.path;
   if (file_name==false)
      return;
   showToastr('success', "Rendering board...");
   // save the path to the generated file, should user want to download it
   generatedFilePath = file_name;  

   var formData = new FormData();
   formData.append("fileName", file_name);
   var req = {
      url: "/renderboard",
      method: "post",
      processData: false,
      contentType: "application/json",
      dataType: "json",
      data: JSON.stringify({fileName: file_name})
   }
   var promise = $.ajax(req);
   promise.then(renderImageSuccess, serverError);
};

function renderImageSuccess(response)
{
   toastr.remove();
   var imagePath=response.path;
   var d = new Date();
   var imgid = "img"+d.getTime();
   // delete all contents of div#messages
   $('#placeholder').empty();
   // build the img html element
   var htmlImg = '<img id="'+imgid+'" class="generated-image" src="'+imagePath+'" data-zoom-image="'+imagePath +'" ';
   htmlImg = htmlImg + 'onclick="downloadGeneratedFile()" ';
   htmlImg = htmlImg + 'max-height="650px" height="650px"/>';
   $('#placeholder').prepend(htmlImg);
   // add the new image
   $('#uploadfile').css("border-color", 'lightslategrey');
   hideWaitUpload();
}

function generateNewBoard()
{
   showToastr('success', "Generating board...");
   var req = {
      url: "/generateboard",
      method: "get",
      processData: false,
      contentType: "application/json"
   }
   var promise = $.ajax(req);
   promise.then(requestBoardRendering, serverError);
}

function suggestBoardCompletionOnUpload(response)
{
   uploadedFilePath = response.path;
   suggestBoardCompletion(uploadedFilePath);
}
function suggestAgainBoardCompletion()
{
   if (uploadedFilePath == undefined){
      showToastr('error', "Please upload a board first.")
      return;
   }
   suggestBoardCompletion(uploadedFilePath);
}

function suggestBoardCompletion(filePath)
{
   showToastr('success', "Suggesting board completion...");
   var req = {
      url: "/completeboard",
      method: "post",      
      processData: false,
      contentType: "application/json",
      dataType: "json",
      data: JSON.stringify({fileName: filePath})
   }
   var promise = $.ajax(req);
   promise.then(requestBoardRendering, serverError);
}

function downloadGeneratedFile()
{
   if (generatedFilePath == undefined) {
      showToastr('error', "No files generated yet");
      return;
   }
   var options = {
      method: "post",
      body: JSON.stringify({fileName: generatedFilePath}),
      contentType: "application/json"
   }
   fetch('/downloadfile', options)
      .then((resp) => resp.blob())
      .then((blob) => {
         var url = window.URL.createObjectURL(blob);
         var a = document.createElement("a");
         a.style.display = "none";
         a.href = url;
         // the filename you want
         var filename = generatedFilePath.replace(/^.*[\\\/]/, '')
         a.download = filename;
         document.body.appendChild(a);
         a.click();
         a.remove();
         window.URL.revokeObjectURL(url);
      })
}

function serverError(data) {
   hideWaitUpload();
   uploadedFilePath = undefined;
   generatedFilePath = undefined;
   showToastr('error', data.responseText);
}

function showToastr(toastrType, toastrMessage) {
   toastr.remove();
   if (toastrType == "success")
      toastr.success(toastrMessage);
   else
      toastr.error(toastrMessage);
}
