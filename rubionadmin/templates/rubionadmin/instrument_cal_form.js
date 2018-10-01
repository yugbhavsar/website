
function(modal){
    var Cal = window.rubion.calendar;
    Cal.start = '';
    Cal.end = '';
    $('a.cal-nav', modal.body).click(
	function() {
            $.ajax({
		url: $(this).attr('href'),
		processData: false,
		contentType: false,
		type: 'GET',
		dataType: 'text',
		success: function(response){
                    modal.loadResponseText(response);
		}
            });
	    return false;
	}
    );
    $('form.instrument-cal-form', modal.body).submit(
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
    $('.hourfield', modal.body).click( 
	function( evt ){
	    var self = $(this);
	    if (! ( self.hasClass('unavailable') || 
		    self.parents('table').hasClass('holiday') ||
		    self.parents('table').hasClass('past') 
		  ))
	    {
		var tr = self.parent('tr')
		if (Cal.start == ''){
		    Cal.start = Cal.get_start_date( self );
		    tr.addClass('selected');
		    tr.addClass('selected-first');
		    tr.nextAll().mouseenter( function (evt) {
			var selftr = $(this);
			// remove all classes
			selftr.siblings().add(selftr).removeClass('selected');
			selftr.prevUntil('.selected-first').add(selftr).addClass('selected');
		    });
		    tr.mouseenter(function(){ $(this).siblings().add($(this)).removeClass('selected');});
		}
		else {
		    Cal.end = Cal.get_end_date( self );
		    tr.siblings().add(tr).removeClass('selected').removeClass('selected-first').off("mouseenter");
		    $('#id_start').val(Cal.start).prop("readonly", true).addClass('readonly');
		    Cal.start = '';
		    $('#id_end').val(Cal.end).prop("readonly", true).addClass('readonly');
		    Cal.end = '';
		    $('a[href$="#direct"]').click();
		    
		}
	    }
	}
    );
}
