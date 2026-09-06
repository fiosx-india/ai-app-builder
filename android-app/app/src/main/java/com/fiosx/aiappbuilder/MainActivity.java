package com.fiosx.aiappbuilder;

import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class MainActivity extends AppCompatActivity {

    private EditText baseUrlInput;
    private EditText projectPathInput;
    private EditText commandInput;
    private EditText approvalIdInput;
    private TextView statusView;
    private SharedPreferences preferences;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        preferences = getSharedPreferences("ai_app_builder", MODE_PRIVATE);

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(32, 40, 32, 40);
        root.setBackgroundColor(Color.rgb(16, 21, 31));
        scroll.addView(root);

        TextView title = text("AI App Builder", 28, Color.WHITE);
        root.addView(title);

        TextView subtitle = text("Android Beta • FastAPI Client", 15, Color.LTGRAY);
        root.addView(subtitle);

        root.addView(space(18));

        baseUrlInput = input("Backend URL (example: http://192.168.1.10:8000)");
        baseUrlInput.setText(preferences.getString("base_url", ""));
        root.addView(label("Backend API URL"));
        root.addView(baseUrlInput);

        Button saveUrl = button("Save Backend URL");
        saveUrl.setOnClickListener(v -> {
            preferences.edit().putString("base_url", baseUrlInput.getText().toString().trim()).apply();
            setStatus("Backend URL saved.");
        });
        root.addView(saveUrl);

        Button health = button("Check Backend Status");
        health.setOnClickListener(v -> request("GET", "/", null));
        root.addView(health);

        root.addView(space(14));

        root.addView(label("Project Path"));
        projectPathInput = input("./projects/default");
        projectPathInput.setText("./projects/default");
        root.addView(projectPathInput);

        root.addView(label("AI Command"));
        commandInput = input("Describe the change you want AI App Builder to plan");
        commandInput.setMinLines(3);
        commandInput.setGravity(Gravity.TOP);
        root.addView(commandInput);

        Button createPlan = button("Create Plan");
        createPlan.setOnClickListener(v -> {
            String body = "{\"command\":\"" + escape(commandInput.getText().toString())
                    + "\",\"project_path\":\"" + escape(projectPathInput.getText().toString()) + "\"}";
            request("POST", "/api/command", body);
        });
        root.addView(createPlan);

        root.addView(space(14));

        root.addView(label("Approval ID"));
        approvalIdInput = input("Paste approval_id returned by Create Plan");
        approvalIdInput.setInputType(InputType.TYPE_CLASS_TEXT);
        root.addView(approvalIdInput);

        Button approve = button("Approve Plan");
        approve.setOnClickListener(v -> approvalRequest("/api/approve"));
        root.addView(approve);

        Button reject = button("Reject Plan");
        reject.setOnClickListener(v -> approvalRequest("/api/reject"));
        root.addView(reject);

        Button getApproval = button("Get Approval Status");
        getApproval.setOnClickListener(v -> {
            String id = approvalIdInput.getText().toString().trim();
            if (id.isEmpty()) {
                setStatus("Enter an approval ID first.");
                return;
            }
            request("GET", "/api/approval/" + id, null);
        });
        root.addView(getApproval);

        Button apply = button("Apply Approved Plan");
        apply.setOnClickListener(v -> approvalRequest("/api/apply"));
        root.addView(apply);

        Button validate = button("Validate Project");
        validate.setOnClickListener(v -> {
            String body = "{\"command\":\"validate\",\"project_path\":\""
                    + escape(projectPathInput.getText().toString()) + "\"}";
            request("POST", "/api/validate", body);
        });
        root.addView(validate);

        Button createProject = button("Create Project");
        createProject.setOnClickListener(v -> {
            String body = "{\"command\":\"create project\",\"project_path\":\""
                    + escape(projectPathInput.getText().toString()) + "\"}";
            request("POST", "/api/project", body);
        });
        root.addView(createProject);

        root.addView(space(16));
        root.addView(label("Response / Status"));
        statusView = text("Ready. Configure the backend URL first.", 14, Color.WHITE);
        statusView.setTextIsSelectable(true);
        root.addView(statusView);

        setContentView(scroll);
    }

    private void approvalRequest(String path) {
        String id = approvalIdInput.getText().toString().trim();
        if (id.isEmpty()) {
            setStatus("Enter an approval ID first.");
            return;
        }
        request("POST", path, "{\"approval_id\":\"" + escape(id) + "\"}");
    }

    private void request(String method, String path, String body) {
        String baseUrl = baseUrlInput.getText().toString().trim();
        if (baseUrl.isEmpty()) {
            setStatus("Set the Backend API URL first.");
            return;
        }

        if (baseUrl.endsWith("/")) {
            baseUrl = baseUrl.substring(0, baseUrl.length() - 1);
        }

        final String requestUrl = baseUrl + path;
        setStatus("Connecting to: " + requestUrl);

        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                URL url = new URL(requestUrl);
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod(method);
                connection.setConnectTimeout(15000);
                connection.setReadTimeout(30000);
                connection.setRequestProperty("Accept", "application/json");

                if (body != null) {
                    connection.setDoOutput(true);
                    connection.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                    try (OutputStream os = connection.getOutputStream()) {
                        os.write(body.getBytes(StandardCharsets.UTF_8));
                    }
                }

                int code = connection.getResponseCode();
                BufferedReader reader = new BufferedReader(
                        new InputStreamReader(code >= 400
                                ? connection.getErrorStream()
                                : connection.getInputStream(), StandardCharsets.UTF_8)
                );

                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line).append('\n');
                }
                reader.close();

                final String result = "HTTP " + code + "\n\n" + response;
                runOnUiThread(() -> statusView.setText(result));

            } catch (Exception e) {
                final String error = "Connection failed:\n" + e.getClass().getSimpleName()
                        + "\n" + e.getMessage()
                        + "\n\nCheck that the backend is running and the URL is reachable from the phone.";
                runOnUiThread(() -> statusView.setText(error));
            } finally {
                if (connection != null) connection.disconnect();
            }
        }).start();
    }

    private TextView label(String value) {
        TextView view = text(value, 14, Color.rgb(190, 205, 220));
        view.setPadding(0, 18, 0, 6);
        return view;
    }

    private TextView text(String value, int size, int color) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        view.setPadding(0, 6, 0, 6);
        return view;
    }

    private EditText input(String hint) {
        EditText view = new EditText(this);
        view.setHint(hint);
        view.setHintTextColor(Color.GRAY);
        view.setTextColor(Color.WHITE);
        view.setSingleLine(false);
        view.setBackgroundColor(Color.rgb(30, 39, 52));
        view.setPadding(20, 16, 20, 16);
        return view;
    }

    private Button button(String value) {
        Button view = new Button(this);
        view.setText(value);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.topMargin = 8;
        view.setLayoutParams(params);
        return view;
    }

    private View space(int height) {
        View view = new View(this);
        view.setLayoutParams(new LinearLayout.LayoutParams(1, height));
        return view;
    }

    private void setStatus(String value) {
        if (statusView != null) statusView.setText(value);
    }

    private static String escape(String value) {
        if (value == null) return "";
        return value.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r");
    }
}
