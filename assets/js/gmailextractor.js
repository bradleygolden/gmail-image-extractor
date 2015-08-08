jQuery(function ($) {

	var prog_hidden = true,
		results_hidden = true,
		loc = window.location,
		$prog_container = $(".progress"),
		$prog = $(".progress-bar"),
		$results_container = $(".results"),
		$email = $("#email"),
		$pass = $("#password"),
		$submit = $("#submit"),
		$auth_form = $("#auth-form"),
		$auth_fields = $auth_form.find(":input"),
		$alert = $(".alert"),
		$sync_form = $("#sync-form"),
		$confim_form = $("#confirm-form"),
		$no_confirm_bttn = $confim_form.find("[type=cancel]"),
		$delete = $("#delete"),
		$delete_modal = $("#delete-modal"),
		$select_all = $("#select-all"),
		select_bool = false,
		$image_menu = $("#image-menu"),
		$save = $("#save"),
		$input = $("#input"),
		rewrite_index = null,
		rewrite_total = null,
		feedback = null,
		num_messages = null,
		update_progress = null,
		hide_progress = null,
		update_results = null,
		img_id = null,
		hide_results = null,
		selected_imgs = [],
		encoded_images = [],
		image_names = [],
		pkg_image_count = 0,
		ws = new WebSocket("ws://" + loc.host + "/ws");

	hide_results = function () {

		$results_container.fadeOut();
		results_hidden = true;
	};

	//displays images in the browser as they are found in the users mailbox
	update_results = function (msg_id, img_id, enc_img) {

		if (results_hidden) {

			$results_container.show();
			results_hidden = false;
		}

		//decode image from base64 to small image to display in img tag
		var img = new Image();
		img.src = 'data:image/jpeg;base64,' + enc_img;

		//create thumbnail for image to be displayed in
		//create a unique img_id for the purpose of selecting each image
		$results_container.append('<div class="col-xs-6 col-md-3">' + 
								  '<div class="thumbnail">' +
								  '<input class="img-checkbox" id="' + img_id + 
								  '" name="' + msg_id + '" type="checkbox" style="display:none;"">' +
								  '<a href="javascript:void(0)" onclick="previewImage(\''+img.src+'\')">' + 
								  '<img src="' + img.src + '">' + 
								  '</a>' +
								  '</div>' +
								  '</div>');
	};

	hide_progress = function () {
		$prog_container.fadeOut();
		prog_hidden = true;
	};

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

	feedback = function (msg, additional_message) {

		$alert.removeClass("alert-info").removeClass("alert-warning");
		$alert.show();

		if (msg.ok) {

			$alert.addClass("alert-info");

		} else {

			$alert.addClass("alert-warning");

		}

		if (additional_message) {

			$alert.html("<p>" + msg.msg + "</p><p>" + additional_message + "</p>");

		} 

		else if (msg.link) {

			$alert.html(msg.link);
		}
		
		else {

			$alert.text(msg.msg);

		}

		

		return;
	};

	previewImage = function (image_body) {

		$("#imagePreview").attr("src", image_body);
		$("#imageModal").modal('show', function(){

			$(this).find('.modal-body').css({

				width:'auto', //probably not needed
				height:'auto', //probably not needed 
				'max-height':'100%'
			});
		});
	};

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
	$delete_modal.click(function () {

		var params = JSON.stringify({
			"type" : "delete",
			"image" : selected_imgs
		});

		ws.send(params);

		$("#deleteModal").modal('hide');
	});

	$auth_form.submit(function () {

		var params = JSON.stringify({
			"email": $email.val(),
			"pass": $pass.val(),
			"type": "connect",
			"limit": 0,
			"simultaneous": 10,
			"rewrite": 1
		});

		$auth_fields.attr("disabled", "disabled");
		ws.send(params);

		return false;
	});

	$sync_form.submit(function () {

		var params = JSON.stringify({
			"type": "sync"
		});

		$(this).find("[type=submit]").attr("disabled", "disabled");
		ws.send(params);

		return false;
	});


	$confim_form.submit(function () {

		var params = JSON.stringify({
			"type": "confirm",
		});

		$(this).find("button").attr("disabled", "disabled");
		ws.send(params);

		return false;
	});

	$no_confirm_bttn.click(function () {

		feedback({msg: "Thank you for your participation in this study."});
		$confim_form.fadeOut();
		return false;
	});

	var count_checked = function() {
		return $( "input:checked" ).length;
	};

	String.prototype.capitalizeFirstLetter = function(){

		return this.charAt(0).toUpperCase() + this.slice(1);
	};

	var changeBtnState = function(value, msg){

		msg = msg.toLowerCase();

		var $type = $( "#" + msg);

		msg = msg.capitalizeFirstLetter();

		if(value === 0){

			$type.addClass("disabled");
			$type.text(msg + " Image");
		}
		else if(value === 1){

			$type.removeClass("disabled");
			$type.text(msg + " Image");
		}
		else if(value > 1){

			$type.removeClass("disabled");
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

	packets_complete = function(msg){

		if(build_image_packets(msg.packet_count, msg.total_images, msg.images, msg.image_names)){
			hide_progress();
			return true;
		}
		else
			return false;
	};

	build_image_packets = function(curr_count, total_images, images, names){

		if (curr_count == 0 || total_images == 0 || images.length == 0 || names.length == 0){
			return;
		}

		if (curr_count == total_images){

			for (i = 0; i < names.length; i++){
				image_names.push(names[i]);
				encoded_images.push(images[i]);
			}

			return true;
		}

		else {

			for (i = 0; i < names.length; i++){
				image_names.push(names[i]);
				encoded_images.push(images[i]);
			}
			return false;
		}
	};

	function save_file(names, images)
	{
		if (names.length != images.length){
			console.error("Images names do not match up with the nubmer of images. They must be equal!");
			return;
		}

		var total_images = images.length;
		var zipped_images = 0;
		var count = 2;
		var prev = count;
		var duplicate_tag = "";
		var msg = {"ok": true, msg: "Creating zip file..."};
		feedback(msg);

		try {
			//create JSZip object
			var zip = new JSZip();

			//add images and their names to zip file
			for (var i = 0; i < images.length; i++)
			{
				try {
					//manange duplicate images
					while(zip.file(names[i]).name != null)
						{
							//console.log("duplicate image exists:", names[i]);
							//get img_type i.e. .jpg
							var img_type = names[i].slice(names[i].length - 4,names[i].length);
							//console.log("image extension:", img_type);

							//remove img_type image.jpg -> image
							names[i] = names[i].slice(0,names[i].length-4);
							//console.log("removed extension:", names[i]);

							//add a duplicate image tag
							names[i] = names[i] + "(" + count + ")";
							//console.log("duplicate tag added:", names[i]);

							//add image extension
							names[i] = names[i] + img_type;
							//console.log("image extension added:", names[i]);

							count++;
						}
				} catch (e){
					//do nothing here, there is no duplicate named zip object
				}

				count = 2;
				zip.file(names[i], images[i], {base64: true});
				zipped_images += 1;
				//console.log("zipped:", names[i], zipped_images, "total", total_images);

			}

			var content = null;

			var content = zip.generate({type:"blob"});

			console.log("zip file size", (content.size/1000000).toFixed(2) + "mb");
			//display os save dialoge using FileSaver.js

			msg.msg = "Zip file successfully created!";
			feedback(msg);
			saveAs(content, "gmail_images.zip");
		}
		catch (e){
			msg.msg = "Zip compilation failed...";
			msg.ok = false;
			feedback(msg);
			console.log("An error has occured during the zip process:", e);
		}

		//reset package size count
		pkg_image_count = 0;

		//reset selected image names
		image_names = [];

		//reset selected images
		encoded_images = [];

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

	ws.onmessage = function (evt) {
		var msg = JSON.parse(evt.data);

		switch (msg['type']) {

			case "connect":
				feedback(msg);
			if (!msg.ok) {
				$auth_fields.removeAttr("disabled");
			} else {
				$auth_form.fadeOut();
			}
			break;

			case "count":
				feedback(msg);
			num_messages = msg.num;
			break;

			case "image":
				update_results(msg.msg_id, msg.img_id, msg.enc_img);
			break;

			case "image-packet":
				feedback(msg);
				update_progress(msg.packet_count, msg.total_images);
				if(packets_complete(msg)){
					save_file(image_names, encoded_images);
				}
			break;

			case "downloading":
				feedback(msg);
			update_progress(msg.num, num_messages);
			break;

			case "download-complete":
				feedback(msg, "Please check all attachments you'd like removed from your GMail account");
			hide_progress();
			$image_menu.fadeIn();
			$('.img-checkbox').show()
			//$sync_form.fadeIn();
			break;

			case "zip":
				feedback(msg);

			case "image-removed":
				remove_image(msg.gmail_id, msg.image_id)
			break;

			case "packet-progress":
				//feedback(msg);
				//update_progress(msg.num, msg.messages);
			break;

			case "file-checking":
				feedback(msg);
			update_progress();
			//$sync_form.fadeOut();
			break;

			case "file-checked":
				rewrite_total = msg.num;
			hide_progress();
			$alert.hide();
			$confim_form
			.fadeIn()
			.find("p")
			.text("Are you sure you want to remove " + rewrite_total + " images from your email account?  This action is irreversable.");
			break;

			case "removing":
				$confim_form.fadeOut();
			feedback(msg);
			update_progress(++rewrite_index, rewrite_total);
			break;

			case "removed":
				feedback(msg);
			break;

			case "finished":
				feedback(msg);
			hide_progress();
			break;
		}
	};

});
