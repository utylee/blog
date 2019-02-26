//
// Class Modal()
var Modal = function(div_id) {
	this.div_id = div_id;
}

Modal.prototype.text = function(e) { this.context = e; }
Modal.prototype.show = function() { $('#'+this.div_id).modal(); }
Modal.prototype.hide = function() { $('#'+this.div_id).modal('hide'); }


//
// Class InfoModal(Modal)
var InfoModal = function() {
	Modal.call(this, 'modal_info');
}
InfoModal.prototype = Object.create(Modal.prototype);
InfoModal.prototype.constructor = InfoModal;
InfoModal.prototype.show_time = function(duration) {
	$('#'+this.div_id).modal();
	var that = this;
	setTimeout(function() {$("#"+that.div_id).modal('hide');}, duration);
	document.getElementById('modal_info_text').innerHTML = this.context;
}
InfoModal.prototype.Show = function(text, duration) {
	this.text(text);
	this.show_time(duration);
}

//
// Class LogoutModal(Modal)
var LogoutModal = function() {
	Modal.call(this, 'modal_logout');
}
LogoutModal.prototype = Object.create(Modal.prototype);
LogoutModal.prototype.constructor = LogoutModal;
LogoutModal.prototype.Show = function(name) {
	document.getElementById('logout_name').innerHTML = name;
	this.show();
}


/*
var logout_modal = new LogoutModal("modal_logout", "로그아웃 합니까?");
*/


