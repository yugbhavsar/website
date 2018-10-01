function(modal){
    $('form.rejection-form', modal.body).submit(function() {
        var formdata = new FormData(this);
        $.ajax({
            url: this.action,
            data: formdata,
            processData: false,
            contentType: false,
            type: 'POST',
            dataType: 'text',
            success: function(response){
		console.log(response);
                modal.loadResponseText(response);
            }
        });
    
	
	return false;
    });
}
