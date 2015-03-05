package test.appmsgbridge;

import java.util.UUID;

import org.json.JSONArray;
import org.json.JSONObject;
import test.appmsgbridge.R;

import de.tavendo.autobahn.WebSocketConnection;
import de.tavendo.autobahn.WebSocketException;
import de.tavendo.autobahn.WebSocketHandler;
import android.annotation.SuppressLint;
import android.annotation.TargetApi;
import android.app.Notification;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;
import android.support.v4.app.NotificationCompat;
import android.util.Log;

@TargetApi(Build.VERSION_CODES.HONEYCOMB)
public class ForegroundService extends Service {
	private static final String LOG_TAG = "ForegroundService";



	private final String TAG = "Svc WS";
	private final WebSocketConnection mConnection = new WebSocketConnection();
	WS ws;

	private void start(String wsuri) {
		ws = new WS(this.getApplicationContext(), wsuri);
		try {
			mConnection.connect(wsuri, ws);
		} catch (WebSocketException e) {

			Log.d(TAG, e.toString());
		}

	}

	private class WS extends WebSocketHandler {
		public String wsuri = "";

		public Context ctxt=null;

		public WS(Context c, String wsuri) {
			this.wsuri = wsuri;
			ctxt=c;
		}

		@Override
		public void onOpen() {
			Log.d(TAG, "Status: Connected to " + wsuri);
		}

		@SuppressLint("NewApi")
		@Override
		public void onTextMessage(String payload) {

			try {
				JSONObject jso = new JSONObject(payload);
				String acknack = jso.optString("acknack");
				if (acknack.isEmpty()) {
					String uuid = jso.getString("uuid");
					Integer txid = jso.getInt("txid");
					JSONArray jsa_msg_data = jso.getJSONArray("msg_data");
					Intent i = new Intent("com.getpebble.action.app.RECEIVE");
					Bundle b = new Bundle();
					UUID myuuid = UUID.fromString(uuid);
					b.putSerializable("uuid", myuuid);
					b.putInt("transaction_id", txid);
					b.putString("msg_data", jsa_msg_data.toString());
					i.putExtras(b);
					if (ctxt!=null) {
						ctxt.sendBroadcast(i);
					} else {
						Log.d(TAG,"ctxt was null");
					}
				} else {
					Integer txid = jso.getInt("txid");
					Intent i = null;
					if (acknack.equals("ack")) {
						i = new Intent("com.getpebble.action.app.RECEIVE_ACK");
					} else {
						i = new Intent("com.getpebble.action.app.RECEIVE_NACK");
					}
					i.putExtra("transaction_id", txid);
					//					Bundle b = new Bundle();
					//					UUID myuuid = UUID.fromString(uuid);
					//					b.putSerializable("uuid", myuuid);
					//					b.putInt("transaction_id", txid);
					//					b.putString("msg_data", jsa_msg_data.toString());
					//					i.putExtras(b);
					if (ctxt!=null) {
						ctxt.sendBroadcast(i);
					} else {
						Log.d(TAG,"ctxt was null");
					}

				}
			} catch (Exception ex) {
				ex.printStackTrace();
			}

			Log.d(TAG, "Got ws: " + payload);
		}

		@Override
		public void onClose(int code, String reason) {
			Log.d(TAG, "Connection lost.");
		}
	}



	@Override
	public void onCreate() {
		super.onCreate();
	}

	@Override
	public int onStartCommand(Intent intent, int flags, int startId) {
		if (intent.getAction().equals(Constants.ACTION.STARTFOREGROUND_ACTION)) {
			Log.i(LOG_TAG, "Received Start Foreground Intent ");

			String wsuri=intent.getStringExtra("wsuri");

			if (wsuri!=null) {

				Intent notificationIntent = new Intent(this, MainActivity.class);
				notificationIntent.setAction(Constants.ACTION.MAIN_ACTION);
				notificationIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK
						| Intent.FLAG_ACTIVITY_CLEAR_TASK);
				PendingIntent pendingIntent = PendingIntent.getActivity(this, 0,
						notificationIntent, 0);

				Intent stopIntent = new Intent(this, ForegroundService.class);
				stopIntent.setAction(Constants.ACTION.STOPFOREGROUND_ACTION);
				PendingIntent pstopIntent = PendingIntent.getService(this, 0,
						stopIntent, 0);

				Bitmap icon = BitmapFactory.decodeResource(getResources(),
						R.drawable.ic_launcher);

				Notification notification = new NotificationCompat.Builder(this)
				.setContentTitle("Pebble AppMsg Bridge")
				.setTicker("Pebble AppMsg Bridge")
				.setContentText("Connected")
				.setSmallIcon(R.drawable.ic_launcher)
				.setLargeIcon(
						Bitmap.createScaledBitmap(icon, 128, 128, false))
						.setContentIntent(pendingIntent)
						.setOngoing(true)
						.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Stop",
								pstopIntent).build();
				startForeground(Constants.NOTIFICATION_ID.FOREGROUND_SERVICE,
						notification);

				// Start the ws
				start(wsuri);
			} else {
				Log.d(LOG_TAG,"ForegroundService start will null wsuri");
			}

		} else if (intent.getAction().equals(Constants.ACTION.SENDWS)) {
			Log.i(LOG_TAG, "SendWS");
			String msg = intent.getStringExtra("msg");
			if (mConnection!=null && msg!=null && mConnection.isConnected()) {
				mConnection.sendTextMessage(msg);
			} else {
				Log.d(LOG_TAG,"ForegroundService not sending wsmsg mConnection=" + mConnection + " msg=" + msg);
				
			}
		} else if (intent.getAction().equals(
				Constants.ACTION.STOPFOREGROUND_ACTION)) {
			Log.i(LOG_TAG, "Received Stop Foreground Intent");
			stopForeground(true);
			stopSelf();
		}
		return START_STICKY;
	}

	@Override
	public void onDestroy() {
		super.onDestroy();
		Log.i(LOG_TAG, "In onDestroy");
	}

	@Override
	public IBinder onBind(Intent intent) {
		// Used only in case of bound services.
		return null;
	}
}