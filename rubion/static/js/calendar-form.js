// Logic for calendar-based bookings

window.rubion = {
    calendar : {
	start : '',
	end : '',
	get_start_date : function( field ){
	    return $(field).parents('table').data('day')+' '+$(field).data('start-time');
	},
	get_end_date : function( field ){
	    return $(field).parents('table').data('day')+' '+$(field).data('end-time');
	}
    }
}

$( document ).ready( function(){ 
    $('.hourfield').each( function(){
	$(this).click( function( evt ){
	    var Cal = window.rubion.calendar;
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
		    $('#id_end').val(Cal.end).prop("readonly", true).addClass('readonly');

		    $('#calendarcontainer').addClass('is-posted').removeClass('is-empty');

		}
		    





	    }
	});

    });
})
