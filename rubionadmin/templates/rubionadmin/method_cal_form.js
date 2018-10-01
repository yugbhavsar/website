function(modal){
    $('form.method-cal-form', modal.body).submit(
	function( evt ){
	    evt.preventDefault();
	    var formdata = new FormData(this);
	    $.ajax({
		url : this.action,
		processData: false,
		contentType: false,
		data: formdata,
		method: 'POST',
		dataType: 'text',
		success: function(response){
                    modal.loadResponseText(response);
		}
	    });
	    return false;
	}
    );
}
