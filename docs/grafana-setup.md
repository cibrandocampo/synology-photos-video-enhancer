# Monitoring with Grafana

The project includes optional Grafana integration for visualizing transcoding statistics and monitoring the database. This feature is completely optional and can be enabled by using `docker-compose.yml` (which includes Grafana) instead of `docker-compose-without-grafana.yml`.

## Setting Up Grafana

1. **Configure Grafana variables in `.env`** (optional, defaults are provided):
   - `GRAFANA_PORT`: Port for Grafana web interface (default: `3000`)
   - `GRAFANA_USER`: Admin username (default: `admin`)
   - `GRAFANA_PASSWORD`: Admin password (default: `admin`)
   - `GRAFANA_PERSISTENCE_PATH`: Path where Grafana data is stored (default: `./grafana-data`)

2. **Start Grafana service:**
   ```bash
   docker compose --profile grafana up -d
   ```

3. **Access Grafana:**
   - **Local access**: Open your browser and go to: `http://localhost:${GRAFANA_PORT:-3000}`
   - **External access (optional)**: To access Grafana from outside your network through a reverse proxy:
     - Go to **Control Panel** -> **Login Portal** -> **Advanced** -> **Reverse Proxy**
     - Add a new reverse proxy rule:
       - **Source**: Configure your domain (e.g., `grafana.yourdomain.com`)
       - **Destination**: Set the port to `${GRAFANA_PORT:-3000}` (the Docker port)
     - If using SSL/HTTPS, assign the certificate as usual (for detailed SSL certificate setup instructions, search online or send an email to [hello@cibran.es](mailto:hello@cibran.es))
   - Login with the credentials configured in `.env` (default: `admin`/`admin`)
   - A form may appear to change the password; you can skip it or set a new password

4. **Configure SQLite Data Source:**
   - The SQLite plugin is automatically installed via `GF_INSTALL_PLUGINS`
   - In the left panel, go to **Connections** -> **Data sources**
   - Search for "SQLite" (it should show as "signed" plugin)
   - Click on "SQLite" to configure it
   - Fill in the **Path** field with: `/data/transcodings.db`
   - Click **Save & Test** and confirm that everything is correct
   - **Note**: If it fails, check the path. If you changed `DATABASE_HOST_PATH` in `.env`, the database location may be different

   ![SQLite Data Source Configuration](https://raw.githubusercontent.com/cibrandocampo/synology-photos-video-enhancer/master/docs/images/grafana_database.png)

5. **Create Dashboards:**
   - Go to **Dashboards** in the left panel
   - Create dashboards with queries to visualize:
     - Total videos processed
     - Success/failure rates
     - Videos by status
     - Error details
     - Processing statistics
   - Alternatively, you can import the pre-configured dashboard from `grafana-dashboard.json`:
     - Go to **Dashboards** -> **Import**
     - Upload the `grafana-dashboard.json` file
     - Select your SQLite data source
     - Click **Import**

   ![Full Grafana Dashboard](https://raw.githubusercontent.com/cibrandocampo/synology-photos-video-enhancer/master/docs/images/full_grafana_dashboard.png)

## Additional Resources

- [Grafana Queries Guide](grafana-queries.md) - Ready-to-use SQL queries for dashboards
- [SQLite Database Schema](sqlite-schema.md) - Complete database schema documentation
