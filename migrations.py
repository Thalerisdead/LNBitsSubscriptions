async def m001_initial(db):
    """
    Initial subscriptions tables.
    """
    await db.execute(
        """
        CREATE TABLE subscriptions.plans (
            id TEXT PRIMARY KEY,
            wallet TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            amount INTEGER NOT NULL,
            interval TEXT NOT NULL,
            trial_days INTEGER DEFAULT 0,
            max_subscriptions INTEGER,
            active_subscriptions INTEGER DEFAULT 0,
            webhook_url TEXT,
            success_message TEXT,
            success_url TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    await db.execute(
        """
        CREATE TABLE subscriptions.subscriptions (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL REFERENCES subscriptions.plans (id),
            wallet TEXT NOT NULL,
            subscriber_email TEXT,
            subscriber_name TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            current_period_start TIMESTAMP NOT NULL,
            current_period_end TIMESTAMP NOT NULL,
            trial_end TIMESTAMP,
            cancel_at_period_end BOOLEAN DEFAULT FALSE,
            canceled_at TIMESTAMP,
            metadata TEXT,
            last_payment_id TEXT,
            last_payment_date TIMESTAMP,
            failed_payment_count INTEGER DEFAULT 0,
            next_payment_date TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    await db.execute(
        """
        CREATE TABLE subscriptions.payments (
            id TEXT PRIMARY KEY,
            subscription_id TEXT NOT NULL REFERENCES subscriptions.subscriptions (id),
            payment_hash TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            period_start TIMESTAMP NOT NULL,
            period_end TIMESTAMP NOT NULL,
            payment_date TIMESTAMP,
            failure_reason TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Create indexes for better performance
    await db.execute(
        "CREATE INDEX idx_plans_wallet ON subscriptions.plans (wallet);"
    )
    await db.execute(
        "CREATE INDEX idx_subscriptions_plan_id ON subscriptions.subscriptions (plan_id);"
    )
    await db.execute(
        "CREATE INDEX idx_subscriptions_wallet ON subscriptions.subscriptions (wallet);"
    )
    await db.execute(
        "CREATE INDEX idx_subscriptions_status ON subscriptions.subscriptions (status);"
    )
    await db.execute(
        "CREATE INDEX idx_subscriptions_next_payment ON subscriptions.subscriptions (next_payment_date);"
    )
    await db.execute(
        "CREATE INDEX idx_payments_subscription_id ON subscriptions.payments (subscription_id);"
    )
    await db.execute(
        "CREATE INDEX idx_payments_hash ON subscriptions.payments (payment_hash);"
    )

    # Add security constraints
    await db.execute(
        "ALTER TABLE subscriptions.plans ADD CONSTRAINT check_amount_positive CHECK (amount > 0);"
    )
    await db.execute(
        "ALTER TABLE subscriptions.plans ADD CONSTRAINT check_trial_days_non_negative CHECK (trial_days >= 0);"
    )
    await db.execute(
        "ALTER TABLE subscriptions.plans ADD CONSTRAINT check_trial_days_max CHECK (trial_days <= 365);"
    )
    await db.execute(
        "ALTER TABLE subscriptions.plans ADD CONSTRAINT check_max_subscriptions_positive CHECK (max_subscriptions IS NULL OR max_subscriptions > 0);"
    )
    await db.execute(
        "ALTER TABLE subscriptions.plans ADD CONSTRAINT check_name_length CHECK (LENGTH(name) >= 1 AND LENGTH(name) <= 100);"
    )
    await db.execute(
        "ALTER TABLE subscriptions.plans ADD CONSTRAINT check_valid_interval CHECK (interval IN ('daily', 'weekly', 'monthly', 'yearly'));"
    )
    
    # Create audit table for security events
    await db.execute(
        """
        CREATE TABLE subscriptions.security_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id TEXT,
            ip_address TEXT,
            details TEXT,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    
    await db.execute(
        "CREATE INDEX idx_audit_timestamp ON subscriptions.security_audit (timestamp);"
    )
    await db.execute(
        "CREATE INDEX idx_audit_event_type ON subscriptions.security_audit (event_type);"
    ) 