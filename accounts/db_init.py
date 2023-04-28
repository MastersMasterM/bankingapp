import psycopg2


# Connect to your postgres DB
conn = psycopg2.connect(dbname="test", user="postgres", password="ma1379?")

with conn.cursor() as curs:
    # Execute a query that creates all the tables
    curs.execute("""
    CREATE TYPE job AS ENUM ('client', 'employee');
    CREATE TYPE a_type AS ENUM ('deposit', 'withdraw', 'transfer', 'interest');

    CREATE TABLE account(
        username text PRIMARY KEY,
        accountNumber CHAR (16) UNIQUE NOT NULL,
        password VARCHAR (50) NOT NULL,
        first_name text NOT NULL,
        last_name text NOT NULL,
        national_id CHAR (10),
        date_of_birth TIMESTAMP,
        u_type job,
        interest_rate INT
    );

    CREATE TABLE login_log(
        username text NOT NULL,
        login_time TIMESTAMP NOT NULL,
        CONSTRAINT login_log_username_fkey FOREIGN KEY (username)
          REFERENCES account (username) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION
    );

    CREATE TABLE transactions(
        t_type a_type NOT NULL,
        transaction_time TIMESTAMP NOT NULL,
        from_an CHAR (16),
        to_an CHAR (16),
        amount INT NOT NULL,
        CONSTRAINT from_accountNum_fkey FOREIGN KEY (from_an)
          REFERENCES account (accountNumber) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION,
        CONSTRAINT to_accountNum_fkey FOREIGN KEY (to_an)
          REFERENCES account (accountNumber) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION
    );

    CREATE TABLE latest_balances(
        accountNumber CHAR (16) NOT NULL UNIQUE,
        amount INT NOT NULL,
        CONSTRAINT balance_accountNum_fkey FOREIGN KEY (accountNumber)
          REFERENCES account (accountNumber) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION
    );

    CREATE TABLE snapshot_log(
        snapshot_id serial NOT NULL UNIQUE,
        snapshot_timestamp TIMESTAMP NOT NULL
    );

    CREATE TABLE snapshot_id(
      id INT NOT NULL,
      accountNumber CHAR (16) NOT NULL,
      amount INT NOT NULL,
      CONSTRAINT id_log_fkey FOREIGN KEY (id)
          REFERENCES snapshot_log (snapshot_id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION,
      CONSTRAINT accnum_lbal_fkey FOREIGN KEY (accountNumber)
          REFERENCES latest_balances (accountNumber) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION    
    );
    """)
    print(curs.statusmessage)
    curs.execute('commit')
    curs.execute("""
    --Register

--Function That Generates a hash string based on firstname and lastname as username and generate accountnumber
CREATE EXTENSION pgcrypto;
CREATE OR REPLACE FUNCTION generate_user_id() RETURNS TRIGGER AS $$
DECLARE r_s text;
BEGIN
	r_s = (Select crypt('a', gen_salt('des')));
    NEW.username := CONCAT(NEW.last_name,r_s);
    NEW.accountnumber := LPAD(FLOOR(RANDOM()*999999999999999)::text,16,'1');
    NEW.password = md5(NEW.password);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

--A trigger that set the username and account number
CREATE TRIGGER generate_user_id_trigger
BEFORE INSERT ON account
FOR EACH ROW
EXECUTE FUNCTION generate_user_id();

--Function That Generates a record in latest_balance for each row 
CREATE OR REPLACE FUNCTION init_balance() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO latest_balances
	VALUES(NEW.accountnumber,'0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

--A trigger that run latest_balance function
CREATE TRIGGER init_balance_trigger
AFTER INSERT ON account
FOR EACH ROW
EXECUTE FUNCTION init_balance();

--Print Username After Insertion
CREATE OR REPLACE FUNCTION getter() RETURNS TRIGGER AS $$
BEGIN
	RAISE NOTICE '%', NEW.username;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER getter_trigger
AFTER INSERT ON account
FOR EACH ROW
EXECUTE FUNCTION getter();

--Procedure register
CREATE OR REPLACE PROCEDURE register(
    password varchar (50),
    first_name text,
    last_name text,
    national_id char(10),
    date_of_birth timestamp,
    utype job,
    intrest_rate integer
)
language plpgsql    
as $$
begin
	   IF (utype = 'employee') THEN
			intrest_rate = 0;
		END IF;
       IF (extract(year FROM age(NOW()::timestamp, date_of_birth)) > 13) THEN
        	INSERT into account(password,first_name,last_name,national_id,date_of_birth,u_type,interest_rate) 
        	VALUES(password,first_name,last_name,national_id,date_of_birth,utype,intrest_rate);
		ELSE
			RAISE NOTICE 'Your Age is less than 13';
		END IF;
		
end;$$;
----------------------------------------------------------------------------------------------------------

--Login
CREATE OR REPLACE PROCEDURE login(
    password_i varchar (50),
    username_i varchar(20)
)
language plpgsql    
as $$
begin
        IF EXISTS (SELECT username, password
        FROM account
        WHERE username = username_i) THEN
            IF EXISTS (SELECT username, password
        	FROM account
        	WHERE username = username_i and password = md5(password_i)) THEN
                INSERT into login_log
				VALUES(username_i,NOW());
				RAISE NOTICE 'Successful';
            ELSE
                RAISE NOTICE 'Password is wrong';
            END IF;
        ELSE
           RAISE NOTICE 'User doesnt exits';
        END IF;
end;$$;

---------------------------------------------------------------------------------------------------------

--Deposit
CREATE OR REPLACE PROCEDURE deposit(
    to_acc varchar (16),
    amount_num INT
)
language plpgsql    
as $$
begin
    INSERT INTO transactions(t_type,transaction_time,to_an,amount) VALUES
    ('deposit',NOW(),to_acc,amount_num);
end;$$;

--Withdraw
CREATE OR REPLACE PROCEDURE withdraw(
    from_acc varchar (16),
    amount_num INT
)
language plpgsql    
as $$
begin
    INSERT INTO transactions(t_type,transaction_time,from_an,amount) VALUES
    ('withdraw',NOW(),from_acc,amount_num);
end;$$;

--Transfer
CREATE OR REPLACE PROCEDURE transfer(
    from_acc varchar (16),
    to_acc varchar (16),
    amount_num INT
)
language plpgsql    
as $$
begin
    INSERT INTO transactions(t_type,transaction_time,from_an,to_an,amount) VALUES
    ('transfer',NOW(),from_acc,to_acc,amount_num);
end;$$;

--payment_interest
CREATE OR REPLACE PROCEDURE payment_interest(
)
language plpgsql    
as $$
begin
    INSERT INTO transactions(t_type,transaction_time,to_an,amount) 
		SELECT 'interest',NOW(),account.accountnumber,FLOOR(account.interest_rate*latest_balances.amount/100)
    	FROM account INNER JOIN latest_balances ON account.accountnumber = latest_balances.accountnumber;
end;$$;

--balances_update
CREATE OR REPLACE PROCEDURE balances_update(
)
language plpgsql    
as $$
DECLARE temprow RECORD;
begin
    FOR temprow in (SELECT * FROM transactions
    WHERE transaction_time > (SELECT snapshot_timestamp FROM snapshot_log ORDER BY snapshot_id DESC LIMIT 1)
    ORDER BY transaction_time) LOOP
        IF temprow.t_type = 'deposit' THEN
            UPDATE latest_balances SET amount = amount + temprow.amount WHERE accountnumber = temprow.to_an;
        ELSEIF temprow.t_type = 'withdraw' THEN 
			IF (SELECT amount from latest_balances WHERE accountnumber = temprow.from_an) >= temprow.amount THEN
			UPDATE latest_balances SET amount  = amount - temprow.amount WHERE accountnumber = temprow.from_an;
            ELSE
			RAISE NOTICE 'Your Balance is not enough';
            END IF;
        ELSEIF temprow.t_type = 'transfer' THEN
             IF (SELECT amount from latest_balances WHERE accountnumber = temprow.from_an) >= temprow.amount THEN 
                UPDATE latest_balances SET amount  = amount - temprow.amount WHERE accountnumber = temprow.from_an;
                UPDATE latest_balances SET amount  = amount + temprow.amount WHERE accountnumber = temprow.to_an;
            ELSE RAISE NOTICE 'Your Balance is not enough';
            END IF;
        ELSEIF temprow.t_type = 'interest' THEN
            UPDATE latest_balances SET amount = amount + temprow.amount WHERE accountnumber = temprow.to_an;
        END IF;
   END LOOP;
end;$$;


--Copy data to snapshot_log
CREATE OR REPLACE FUNCTION slog() RETURNS VOID AS $$
DECLARE lsid INT;
BEGIN
    lsid = (SELECT snapshot_id FROM snapshot_log ORDER BY snapshot_id DESC LIMIT 1);
    INSERT INTO snapshot_log
    VALUES(lsid + 1,NOW());
    RETURN;
END;
$$ LANGUAGE plpgsql;

--Copy data to snapshot_id
CREATE OR REPLACE FUNCTION copy_log() RETURNS TRIGGER AS $$
DECLARE lsid INT;
BEGIN
    PERFORM slog();
    lsid = (SELECT snapshot_id FROM snapshot_log ORDER BY snapshot_id DESC LIMIT 1);
    INSERT INTO snapshot_id
    VALUES(lsid,NEW.accountnumber,NEW.amount);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


--Snapshot logging trigger
CREATE TRIGGER snapshot_logging
BEFORE UPDATE ON latest_balances
FOR EACH ROW
EXECUTE FUNCTION copy_log();

--Procedure Check Balance
CREATE OR REPLACE PROCEDURE balance_checks(
 	OUT res INT,
	accNum CHAR (16)
)
language plpgsql    
as $$
begin
    res = (SELECT amount FROM latest_balances
    WHERE accountNumber = accNum);
end;$$;
    """)
    print(curs.statusmessage)
    curs.execute('commit')
