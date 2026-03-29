// Cemetery Management Client Scripts

// GPS Capture for Burial Plot
frappe.ui.form.on('Burial Plot', {
	capture_gps: function(frm) {
		if (!navigator.geolocation) {
			frappe.msgprint(__('Geolocation is not supported by your browser.'));
			return;
		}

		frappe.show_alert({message: __('Acquiring GPS position...'), indicator: 'blue'});

		navigator.geolocation.getCurrentPosition(
			function(position) {
				frm.set_value('latitude', position.coords.latitude);
				frm.set_value('longitude', position.coords.longitude);
				frappe.show_alert({
					message: __('GPS coordinates captured: {0}, {1}', [
						position.coords.latitude.toFixed(6),
						position.coords.longitude.toFixed(6)
					]),
					indicator: 'green'
				});
			},
			function(error) {
				var msg = __('Unable to retrieve GPS position.');
				switch(error.code) {
					case error.PERMISSION_DENIED:
						msg = __('Location permission denied. Please allow location access.');
						break;
					case error.POSITION_UNAVAILABLE:
						msg = __('Location information unavailable.');
						break;
					case error.TIMEOUT:
						msg = __('Location request timed out.');
						break;
				}
				frappe.msgprint(msg);
			},
			{
				enableHighAccuracy: true,
				timeout: 10000,
				maximumAge: 0
			}
		);
	}
});

// Calendar view colors for Cemetery Work Order
frappe.ui.form.on('Cemetery Work Order', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 0 && frm.doc.status === 'Open') {
			frm.add_custom_button(__('Start Work'), function() {
				frm.set_value('status', 'In Progress');
				frm.save();
			});
		}
		if (frm.doc.docstatus === 0 && frm.doc.status === 'In Progress') {
			frm.add_custom_button(__('Mark Complete'), function() {
				frm.set_value('status', 'Completed');
				frm.set_value('completion_date', frappe.datetime.get_today());
				frm.save();
			});
		}
	}
});
