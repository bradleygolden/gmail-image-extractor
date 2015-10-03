jQuery(function ($) {

	//TODO - force delete to delete images from the frond end and
	// queue a removal in the backend

	var prog_hidden = true,
	loc = window.location,
	$prog_container = $(".progress"),
	$prog = $(".progress-bar"),
	$results_container = $(".results"),
	$status = $(".status"),
	$status = $(".status"),
	$alert = $(".alert"),
	$download_link = $(".download-link"),
	timer = null,
	$stop = $("#stop"),
	$rescan = $("#rescan"),
	$delete_confirmed = $("#delete-confirmed"),
	$select_all = $("#select-all"),
	select_bool = false,
	$images_menu = $("#images-menu"),
	$save = $("#save"),
	$pager_container = $(".wrapper");
	feedback = null,
	selected_imgs = [],
	download_complete = false,
	num_attachments_found = 0,
	stopped = false,
	images_per_page = 1,
	ws = new WebSocket("ws://" + loc.host + "/ws");

	//window.onload = function(){
	connect = function(){

		var params = JSON.stringify({
			"type": "connect",
			"limit": 0,
			"simultaneous": 10,
			"rewrite": 1
		});

		ws.send(params);

	};

	//listen for images as they populate, clear this interval once
	//all images have been displayed
	is_download_complete_interval = window.setInterval(function(){
		count_attachments = 0;

		if (download_complete && num_attachments_found > 0){
			//enable select all button
			show_select_all();
		}

		if (download_complete){
			count_attachments = show_checkboxes();
		}

		if (count_attachments > 0 && count_attachments == num_attachments_found){

			window.clearInterval(is_download_complete_interval);
		}
	}, 100);

	show_select_all = function(){
		$select_all.removeClass("disabled");
		$select_all.prop('disabled', false);
	};

	show_checkboxes = function(){
		count_attachments = 0;
		$('.img-checkbox').each(function(){
			$(this).show();
			count_attachments += 1;
		});
		return count_attachments;
	};

	count_images = function(){
		return $('.thumbnail').length;
	}

	window.onload = function(){
		$('#save').prop('disabled', true);
		$('#delete').prop('disabled', true);
		$('#select-all').prop('disabled', true);
		$('#pager-next').prop('disabled', true);
		$('#pager-prev').prop('disabled', true);
	};

	//displays images in the browser as they are found in the users mailbox
	update_results = function (img) {

		//decode image from base64 to small image to display in img tag
		//var thumb_img = new Image();
		img.src = 'data:image/jpeg;base64,' + img.preview;

		//create thumbnail for image to be displayed in
		$results_container.append($thumbnail(img));
	};

	$thumbnail = function(img) {

		return ('<div class="col-xs-6 col-md-3 grid-item">' +
		'<div class="thumbnail">' +
		'<input class="img-checkbox" id="' + img.id +
		'" name="' + img.msg_id + '" type="checkbox" style="display:none">' +
		'<a href="javascript:void(0)" onclick="previewImage(\''+img.src+'\')">' +
		'<img src="' + img.src + '">' +
		'</a>' +
		'</div>' +
		'</div>');
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

	//used to display status messages to the user
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
		var maxTime = 60000 * (minutes);
		var perc = 0;

		var start = new Date();
		var timeoutVal = Math.floor(maxTime/100);

		animateUpdate();

		function updateProgress(percentage) {
			percentage = percentage/100.0;
			timeRemaining = Math.round(minutes - (minutes * percentage));
			try{
				//percentage_str = parseInt((1-percentage).toFixed(2)*100, 10) + "";
				$('.circle').circleProgress('value', percentage);
				$('.circle-text').text(timeRemaining + "min");
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
			else {
				//end the timer and remove the save link
				hide_download_link();
			}
		}
	};

	hide_download_link = function(){
		clearTimeout(timer);
		$download_link.empty();
		$download_link.hide();
	}

	/**********************************************
	Begin click functions
	**********************************************/

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
			$("#select-all").text("Deselect All ");
			$("#select-all").append("<i class='fa fa-square-o'></i>");

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
			$("#select-all").text("Select All ");
			$("#select-all").append("<i class='fa fa-check-square-o'></i>");
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

	$stop.click(function() {

		stopped = true;
		download_complete = true;
		var add_msg = count_images_message();

		hide_stop_btn();
		show_rescan_btn();
		hide_progress();
		num_attachments_found = count_images();

		var msg = {
			"ok": true,
			"msg": "Extraction process stopped.",
			"type": "none",
		}

		feedback(msg, add_msg);

		var params = JSON.stringify({
			"type" : "stop",
		});

		ws.send(params);

	});

	//sends currently selected images to the backend for removal
	$delete_confirmed.click(function () {

		var params = JSON.stringify({
			"type" : "delete",
			"image" : selected_imgs
		});

		ws.send(params);

		//closes delete modal
		$("#delete-modal").modal('hide');

		//animate and remove thumnail from front-end
		$('input:checked').closest('.thumbnail').animate({
			opacity: 0.25,
			left: "+=50",
			height: "toggle"
		}, 5000, function() {
			$('input:checked').parents('div').eq(1).remove();
		});
	});

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

		hide_download_link();
	});

	/**********************************************
	End click functions
	**********************************************/

	show_stop_alert = function(){
		stop_msg = "Stopping the extraction process...";
		$status.after("<div id='stopping' class='alert alert-danger'></div>");
		$('#stopping').append(stop_msg);
	};

	hide_stop_alert = function(){
		$('#stopping').remove();
	};

	hide_stop_btn = function(){
		$stop.hide();
	};

	disable_stop_btn = function(){
		$stop.addClass('disabled');
		$stop.prop('disabled', true);
	};

	show_rescan_btn = function(){
		$rescan.show();
	};

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
		var font_awesome_icon = "";

		if(msg.localeCompare("delete") == 0)
		font_awesome_icon = "<i class='fa fa-trash'></i>";
		else if (msg.localeCompare("save") == 0)
		font_awesome_icon = "<i class='fa fa-floppy-o'></i>";

		msg = msg.capitalizeFirstLetter();

		if(value === 0){

			$type.addClass("disabled");
			$type.prop('disabled', true);
			$type.text(msg + " Image ");
			$type.append(font_awesome_icon);
		}
		else if(value === 1){

			$type.removeClass("disabled");
			$type.prop('disabled', false);
			$type.text(msg + " Image ");
			$type.append(font_awesome_icon);
		}
		else if(value > 1){

			$type.removeClass("disabled");
			$type.prop('disabled', false);
			$type.text(msg + " Images ");
			$type.append(font_awesome_icon);
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

	count_images_message = function(){

		msg = "";
		image_count = count_images();
		msg_courtesy = "Please check all attachments that" +
		" you want to remove from your Gmail account."


		if (image_count == 0){
			msg = "Found 0 images."
		}
		else if (image_count == 1){
			msg = "Successfully found 1 image. " + msg_courtesy;
		}
		else {
			msg = "Successfully found " + image_count + " images. " + msg_courtesy;
		}

		return msg;
	};

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
			if (!stopped){
				var img = msg;
				update_results(img);
			}
			break;

			case "downloading":
			if(!stopped){
				feedback(msg);
				update_progress(msg.num, num_messages);
			}
			break;

			case "download-complete":
			if (!stopped){
				feedback(msg, "Please check all attachments that you want to remove from your Gmail account.");
				num_attachments_found = msg.num;
				download_complete = true;
				hide_stop_btn();
				show_rescan_btn();
				hide_progress();
			}
			break;

			case "stopped":
			//handled by $stop.click
			break;

			case "saved-zip":
			feedback(msg);
			startTimer(parseInt(msg.time));
			break;

			case "removed-zip":
			//handled by front end
			//use this if you want to tell the user that the backend removed
			//the zip files succesfully
			break;

			case "image-removed":
			remove_image(msg.gmail_id, msg.image_id)
			break;
		}
	};

});
