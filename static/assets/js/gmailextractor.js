jQuery(function ($) {

	// TODO - Remove image thumbnails from frontend before sending to backend. Server callbacks are too slow..

var prog_hidden = true,
loc = window.location,
$prog_container = $(".progress"),
$prog = $(".progress-bar"),
$results_container = $(".results"),
	// 	$email = $("#email"),
	// 	$pass = $("#password"),
	// 	$submit = $("#submit"),
	// 	$auth_form = $("#auth-form"),
	// 	$auth_fields = $auth_form.find(":input"),
$status = $(".status"),
$download_link = $(".download-link"),
timer = null,
	// 	$sync_form = $("#sync-form"),
	// 	$confim_form = $("#confirm-form"),
	// 	$no_confirm_bttn = $confim_form.find("[type=cancel]"),
  // $delete = $("#delete"),
$delete_confirmed = $("#delete-confirmed"),
$select_all = $("#select-all"),
select_bool = false,
$images_menu = $("#images-menu"),
$save = $("#save"),
	// 	$input = $("#input"),
	// 	rewrite_index = null,
	// 	rewrite_total = null,
feedback = null,
	// 	num_messages = null,
	// 	update_progress = null,
	// 	hide_progress = null,
	// 	update_results = null,
	// 	img_id = null,
	// 	hide_results = null,
selected_imgs = [],
	// 	encoded_images = [],
	// 	image_names = [],
	// 	pkg_image_count = 0,
	ws = new WebSocket("ws://" + loc.host + "/ws");
	//

		//window.onload = function(){
		connect = function(){

			var params = JSON.stringify({
				"type": "connect",
				"limit": 0,
				"simultaneous": 1,
				"rewrite": 1
			});

			ws.send(params);

	};

	window.onload = function(){
		$('#save').prop('disabled', true);
		$('#delete').prop('disabled', true);
	};
	//
	// hide_results = function () {
	//
	// 	$results_container.fadeOut();
	// 	results_hidden = true;
	// };
	//
	//displays images in the browser as they are found in the users mailbox
	update_results = function (msg_id, img_id, enc_img, img_name) {

		//decode image from base64 to small image to display in img tag
		var img = new Image();
		img.src = 'data:image/jpeg;base64,' + enc_img;

		//create thumbnail for image to be displayed in
		$results_container.append(thumbnail(msg_id, img_id, img, img_name));
	};

	thumbnail = function(msg_id, img_id, img, img_name) {
		return ('<div class="col-xs-6 col-md-3">' +
								  '<div class="thumbnail">' +
								  '<input class="img-checkbox" id="' + img_id +
								  '" name="' + msg_id + '" type="checkbox" "">' +
								  '<a href="javascript:void(0)" onclick="previewImage(\''+img.src+'\')">' +
								  '<img src="' + img.src + '">' +
								  '</a>' +
								  '</div>' +
								  '</div>');
	};

	//hides the progress bar
	hide_progress = function () {
		$prog_container.fadeOut();
		prog_hidden = true;
	};

	//updates the progress bar percentage
	update_progress = function (cur, max) {

		if (prog_hidden) {
			$prog_container.fadeIn();
			prog_hidden = false;
		}

		if (!cur && !max) {

			$prog_container.addClass("progress-striped").addClass("active");
			$prog.attr("aria-valuenow", 1)
			.attr("aria-valuemax", 1)
			.css("width", "100%");

		} else {

			$prog_container.removeClass("progress-striped").removeClass("active");
			$prog.attr("aria-valuenow", cur)
			.attr("aria-valuemax", max)
			.css("width", ((cur / max) * 100) + "%");
		}

		return;
	};

	//manages a dialoge at the top of the package
	//used to display messages to the user
	feedback = function (msg, additional_message) {

		$status.removeClass("alert-info").removeClass("alert-warning");
		$status.show();

		if (msg.ok) {

			$status.addClass("alert-info");

		} else {

			$alert.addClass("alert-warning");

		}

		if (additional_message) {

			$status.html("<p>" + msg.msg + "</p><p>" + additional_message + "</p>");

		}

		else {

			$status.text(msg.msg);

		}

		if (msg.link) {
			$download_link.addClass("alert-success");
			$download_link.html(msg.link);
			$download_link.show();
		}

		//display a circle progress timer for save link
		if (msg['type'].localeCompare("saved-zip") == 0){
			$('.circle').circleProgress({
						value: 0.0,
						size: 100,
						fill: {
								gradient: ["red", "orange"]
						}
			});
		}

		return;
	};

	startTimer = function(minutes){
		maxTime = 60000 * minutes

		var start = new Date();
		var timeoutVal = Math.floor(maxTime/100);

		animateUpdate(maxTime);

		function updateProgress(percentage) {
			percentage = percentage/100.0;
			timeRemaining = Math.round(minutes - (minutes * percentage));
			try{
				$('.circle').circleProgress('value', percentage);
				$('.circle-text').text(timeRemaining + "");
			}
			catch(e){
				//do nothing
			}
		}

		function animateUpdate() {
		    var now = new Date();
		    var timeDiff = now.getTime() - start.getTime();
		    var perc = Math.round((timeDiff/maxTime)*100);
		      if (perc <= 100) {
		       updateProgress(perc);
					 clearTimeout(timer);
		       timer = setTimeout(animateUpdate, timeoutVal);
		      }
		}
	};



	previewImage = function (image_body) {

		$("#imagePreview").attr("src", image_body);
		$("#image-modal").modal('show', function(){

			$(this).find('.modal-body').css({

				width:'auto', //probably not needed
				height:'auto', //probably not needed
				'max-height':'100%'
			});
		});
	};

	//selects or deselects all images
	//all images are added to an array or all are removed from an array
	$select_all.click(function(){

		//this.addClass("disabled");

		//select all inputs if not selected
		if(select_bool === false){

			//clear all selected images first
			selected_imgs = []

			//push all images to selected_imgs array
			$("input.img-checkbox").each(function(){
				//set property of each checkbox to checked
				$(this).prop('checked', true);

				var img_info = [$(this).attr("name"), $(this).attr("id")];

				//push selected images to selected images array
				selected_imgs.push(img_info);
			});

			select_bool = true;

			//change name of button to deselect all
			$("#select-all").text("Deselect All");

		}

		//deselect all inputs if selected
		else {

			$("input.img-checkbox").each(function(){
				//set property of each checkbox to checked
				$(this).prop("checked", false);
			});

			select_bool = false;

			//pop all selected images in selected images array
			selected_imgs = [];

			//change name of button to select all
			$("#select-all").text("Select All");
		}
		//change delete button state
		num_checked = count_checked();
		changeBtnState(num_checked, "delete");
		changeBtnState(num_checked, "save");
	});

	//on click sends selected images to server to retreive full sized images
	$save.click(function(){

		var params = {};

		//send all selected images to backend
		params = JSON.stringify({
			"type": "save",
			"image": selected_imgs
		});
		ws.send(params);
	});

	//sends currently selected images to the backend for removal
	//closes delete modal
	$delete_confirmed.click(function () {

		var params = JSON.stringify({
			"type" : "delete",
			"image" : selected_imgs
		});

		ws.send(params);

		$("#delete-modal").modal('hide');
	});

	//helper function that counts the number of images that are selected
	var count_checked = function() {
		return $( "input:checked" ).length;
	};

	//capitalizes the first letter in a string
	String.prototype.capitalizeFirstLetter = function(){

		return this.charAt(0).toUpperCase() + this.slice(1);
	};

	//toggles a button state on the menu depending on how many images are selected
	var changeBtnState = function(value, msg){

		msg = msg.toLowerCase();

		var $type = $( "#" + msg);

		msg = msg.capitalizeFirstLetter();

		if(value === 0){

			$type.addClass("disabled");
			$type.prop('disabled', true);
			$type.text(msg + " Image");
		}
		else if(value === 1){

			$type.removeClass("disabled");
			$type.prop('disabled', false);
			$type.text(msg + " Image");
		}
		else if(value > 1){

			$type.removeClass("disabled");
			$type.prop('disabled', false);
			$type.text(msg + " Images");
		}
		else{

			return; //an error has occured
		}
	};

	remove_image = function(gmail_id, image_id){

		var $image_thumbnail = $('#' + image_id);

		if($image_thumbnail.attr('id') === image_id && $image_thumbnail.attr('name') === gmail_id){

			//delete image thumbnail
			$image_thumbnail.parents('div').eq(1).remove();
		}
		else{

		}
	};

	$(document).on( "click", "input.img-checkbox", function() {

		var img_info = [ $(this).attr("name"), $(this).attr("id") ];
		var is_checked = $(this).prop('checked');
		var num_checked = count_checked();
		var select_bool = false;

		changeBtnState(num_checked, "delete");
		changeBtnState(num_checked, "save");

		//checkbox is clicked, save filename in an array
		if(is_checked){

			selected_imgs.push(img_info);
		}

		//checkbox is unclicked, remove filename from the array
		else {

			var index = -1;
			for (i=0; i<selected_imgs.length; i++){
				if (selected_imgs[i][1].localeCompare(img_info[1]) === 0){
					index = i
				}
			}
			selected_imgs.splice(index, 1);
		}
	});

	$(document).on( "click", "#remove-now", function() {
		var params = {};

		//send all selected images to backend
		params = JSON.stringify({
			"type": "remove-zip"
		});
		ws.send(params);

		//stop timer
		clearTimeout(timer);
	});

	ws.onmessage = function (evt) {
		var msg = JSON.parse(evt.data);

		switch (msg['type']) {

			case "ws-open":
				feedback(msg);
				connect();
				break;

			case "connect":
				feedback(msg);
				if(msg.ok)
					$images_menu.fadeIn();
			break;

			case "count":
				feedback(msg);
			num_messages = msg.num;
			break;

			case "image":
				update_results(msg.msg_id, msg.img_id, msg.enc_img);
			break;

			case "downloading":
				feedback(msg);
			update_progress(msg.num, num_messages);
			break;

			case "download-complete":
				feedback(msg, "Please check all attachments that you want to remove from your Gmail account.");
			hide_progress();
			//$sync_form.fadeIn();
			break;

			case "saved-zip":
				feedback(msg);
				startTimer(parseInt(msg.time)); //30 minutes
				break;

			case "removed-zip":
				$download_link.empty();
				$download_link.hide();
				break;

			case "image-removed":
				remove_image(msg.gmail_id, msg.image_id)
			break;
		}
	};

});
