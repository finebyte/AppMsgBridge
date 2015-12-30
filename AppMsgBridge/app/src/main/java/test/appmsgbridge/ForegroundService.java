package test.appmsgbridge;

import java.net.InetSocketAddress;
import java.net.UnknownHostException;
import java.util.UUID;

import org.java_websocket.WebSocket;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.server.WebSocketServer;
import org.json.JSONArray;
import org.json.JSONObject;
import test.appmsgbridge.R;

import android.annotation.SuppressLint;
import android.annotation.TargetApi;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;
import android.support.v4.app.NotificationCompat;
import android.text.format.Formatter;
import android.util.Log;
import android.widget.TextView;

@TargetApi(Build.VERSION_CODES.HONEYCOMB)
public class ForegroundService extends Service {
	private static final String LOG_TAG = "ForegroundService";

	private final String TAG = "Svc WS";
	private WebSocket mConnection = null;
	private WS ws;

	private void start(String wsuri) {
		Log.d(TAG,"Starting...");
		int port=9011;
		try {
			port = Integer.parseInt(wsuri);
		} catch (Exception e) {

		}

		try {
			ws = new WS(this.getApplicationContext(), port);
			ws.start();
		} catch (Exception ex) {
			Log.d(TAG,"Exception creating server..." + ex);

		}
	}

	private void stop() {
		if (mConnection!=null) {
			mConnection.close();
		}
		if (ws!=null) {
			try {
				ws.stop();
			} catch (Exception e) {

			}
		}
	}

	private void setConnection(WebSocket conn) {
		if (mConnection!=null) {
			mConnection.close();
		}
		mConnection=conn;
	}

	private class WS extends WebSocketServer {

		public Context ctxt=null;

		public WS(Context c, int port) throws UnknownHostException {
			super(new InetSocketAddress(port));
			Log.d(TAG, "Starting WS Server...");
			ctxt=c;
		}

		@Override
		public void onOpen(WebSocket conn, ClientHandshake h) {
			Log.d(TAG, "Status: Connected to " + conn.getRemoteSocketAddress());
			setConnection(conn);
			updateNotification("Connected" + conn.getRemoteSocketAddress());
		}

		@Override
		public void onClose(WebSocket conn, int code, String reason, boolean remote) {
			Log.d(TAG, "Connection lost : " + conn.getRemoteSocketAddress() + " \n" + reason);
			updateNotification("Waiting...");
		}

		@Override
		public void onError(WebSocket conn, Exception ex) {
			Log.d(TAG, "Got error: " + ex);
		}

		@SuppressLint("NewApi")
		@Override
		public void onMessage( WebSocket conn, String payload ) {

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


	}

	Notification notification = null;
	String ip=null;

	@Override
	public void onCreate() {
		super.onCreate();
	}

	public Notification getMyNotification(String text) {

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

		Intent closeIntent = new Intent(this, ForegroundService.class);
		stopIntent.setAction(Constants.ACTION.CLOSEFOREGROUND_ACTION);
		PendingIntent pcloseIntent = PendingIntent.getService(this, 0,
				stopIntent, 0);


		Bitmap icon = BitmapFactory.decodeResource(getResources(),
				R.drawable.ic_launcher);

		WifiManager wm = (WifiManager) getSystemService(WIFI_SERVICE);
		ip = Formatter.formatIpAddress(wm.getConnectionInfo().getIpAddress());

		return new NotificationCompat.Builder(this)
				.setContentTitle("Pebble AppMsg Bridge")
				.setTicker("Pebble AppMsg Bridge")
				.setSubText("ws://"+ip+":9011")
				.setContentText(text)
				.setSmallIcon(R.drawable.ic_launcher)
				.setLargeIcon(
						Bitmap.createScaledBitmap(icon, 128, 128, false))
				.setContentIntent(pendingIntent)
				.setOngoing(true)
				.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Stop",
						pstopIntent)
				.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Close",
						pcloseIntent).build();

	}

	private void updateNotification(String text) {

		Notification notification = getMyNotification(text);

		NotificationManager mNotificationManager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
		mNotificationManager.notify(Constants.NOTIFICATION_ID.FOREGROUND_SERVICE, notification);
	}

	@Override
	public int onStartCommand(Intent intent, int flags, int startId) {
		if (intent.getAction().equals(Constants.ACTION.STARTFOREGROUND_ACTION)) {
			if (ws==null) {
				Log.i(LOG_TAG, "Received Start Foreground Intent ");
				String wsuri = intent.getStringExtra("wsuri");
				if (wsuri != null) {
					startForeground(Constants.NOTIFICATION_ID.FOREGROUND_SERVICE,
							getMyNotification("Waiting..."));
					// Start the ws
					start(wsuri);
				} else {
					Log.d(LOG_TAG, "ForegroundService start will null port");
				}
			}

		} else if (intent.getAction().equals(Constants.ACTION.SENDWS)) {
			Log.i(LOG_TAG, "SendWS");
			String msg = intent.getStringExtra("msg");
			if (mConnection!=null && msg!=null && mConnection.isOpen()) {
				mConnection.send(msg);
			} else {
				Log.d(LOG_TAG,"ForegroundService not sending wsmsg mConnection=" + mConnection + " msg=" + msg);
				
			}
		} else if (intent.getAction().equals(
				Constants.ACTION.STOPFOREGROUND_ACTION)) {
			Log.i(LOG_TAG, "Received Stop Foreground Intent");
			stop();
			NotificationManager mNotificationManager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
			mNotificationManager.cancel(Constants.NOTIFICATION_ID.FOREGROUND_SERVICE);
			stopForeground(true);
			stopSelf();
		} else if (intent.getAction().equals(
				Constants.ACTION.CLOSEFOREGROUND_ACTION)) {
			Log.i(LOG_TAG, "Received Close Foreground Intent");
			if (mConnection!=null) {
				mConnection.close();
			}
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