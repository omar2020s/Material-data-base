<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Repair Material Report</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body class="report-body">
    <div class="report-page">
        <div class="report-header">
            <div>
                <h1>Repair Material Calculation Report</h1>
                <p>Professional material quantity and cost report</p>
            </div>
            <div class="report-meta">
                <strong>Date:</strong> {{ now.strftime('%Y-%m-%d %H:%M') }}<br>
                <strong>Area:</strong> {{ area }} m²
            </div>
        </div>

        <div class="table-wrap">
            <table class="report-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Material</th>
                        <th>Type</th>
                        <th>Consumption</th>
                        <th>Price/kg</th>
                        <th>Qty</th>
                        <th>Cost</th>
                        <th>Notes</th>
                        <th>Data Sheet</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in rows %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ row.material.name }}</td>
                        <td>{{ row.material.material_type or '-' }}</td>
                        <td>{{ '%.4f'|format(row.material.rate) }} kg/m²</td>
                        <td>{{ '%.2f'|format(row.material.price) }}</td>
                        <td>{{ '%.2f'|format(row.qty) }} kg</td>
                        <td>{{ '%.2f'|format(row.cost) }}</td>
                        <td>{{ row.material.notes or '' }}</td>
                        <td>
                            {% if row.material.datasheet %}
                                <a href="{{ row.material.datasheet }}" target="_blank">Open</a>
                            {% else %}
                                -
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="total-box">
            TOTAL COST = {{ '%.2f'|format(total_cost) }}
        </div>

        <div class="print-actions no-print">
            <button onclick="window.print()" class="btn success">Print Report</button>
            <a href="{{ url_for('index') }}" class="btn muted">Back</a>
        </div>
    </div>
</body>
</html>
