function createRejectionModal() {
    var btns = $('.reject-button');
    btns.each( 
	function( ){
	    var form = $(this).parent();
	    console.log(form);
	    form.submit(
		function( evt ) {

		    //Prevent sending the form
		    evt.preventDefault();

		    // get the id 
		    var url_parts = form.attr('action').split('/');
		    var r_url = window.rubionadmin.reject_form_url + url_parts[3] + '/';
		    ModalWorkflow({
			url : r_url,
			responses : {

			},
			onload: {
			    'success' : function(modal, jsonData){
				window.location.href = jsonData['wagtailadmin_home_url'];
			    },
			    'show' : function(modal, jsonData){

				$('form.rejection-form', modal.body).submit(function() {
				    var formdata = new FormData(this);
				    $.ajax({
					url: this.action,
					data: formdata,
					processData: false,
					contentType: false,
					type: 'POST',
					dataType: 'text',
					success: function(response, status, jqXHR){
					    console.log(response);
					    modal.loadResponseText(response, status, jqXHR);
					}
				    });
    				    return false;
				});
			    }

			    

			}
		    }); // ModalWorkflow
		    
		    return false;
		}
	    );
	}
    );
}

$( document ).ready(createRejectionModal);

