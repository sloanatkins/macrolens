--
-- PostgreSQL database dump
--

\restrict pSU1OaIzl5RnI01h9EkoVuhcDOEtmS51wKilHvxoE5RVrcBGh12a4k3KkpJTZNg

-- Dumped from database version 16.14 (Homebrew)
-- Dumped by pg_dump version 16.14 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: raw_macro_indicators; Type: TABLE; Schema: public; Owner: sloanatkins
--

CREATE TABLE public.raw_macro_indicators (
    id integer NOT NULL,
    series_id character varying(20) NOT NULL,
    indicator character varying(50) NOT NULL,
    date date NOT NULL,
    value numeric(12,4),
    ingested_at timestamp with time zone NOT NULL
);


ALTER TABLE public.raw_macro_indicators OWNER TO postgres;

--
-- Name: raw_sector_prices; Type: TABLE; Schema: public; Owner: sloanatkins
--

CREATE TABLE public.raw_sector_prices (
    id integer NOT NULL,
    symbol character varying(10) NOT NULL,
    sector character varying(50) NOT NULL,
    date date NOT NULL,
    open numeric(10,4),
    high numeric(10,4),
    low numeric(10,4),
    close numeric(10,4),
    volume bigint,
    ingested_at timestamp with time zone NOT NULL
);


ALTER TABLE public.raw_sector_prices OWNER TO postgres;

--
-- Name: mart_sector_performance; Type: TABLE; Schema: public; Owner: sloanatkins
--

CREATE TABLE public.mart_sector_performance (
    symbol character varying(10),
    sector character varying(50),
    date date,
    open numeric(10,4),
    high numeric(10,4),
    low numeric(10,4),
    close numeric(10,4),
    volume bigint,
    daily_return_pct numeric,
    fed_funds_rate numeric,
    cpi numeric,
    unemployment_rate numeric,
    yield_spread_10y2y numeric,
    gdp numeric,
    macro_regime text,
    rolling_30d_avg_return numeric
);


ALTER TABLE public.mart_sector_performance OWNER TO postgres;

--
-- Name: raw_macro_indicators_id_seq; Type: SEQUENCE; Schema: public; Owner: sloanatkins
--

CREATE SEQUENCE public.raw_macro_indicators_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.raw_macro_indicators_id_seq OWNER TO postgres;

--
-- Name: raw_macro_indicators_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sloanatkins
--

ALTER SEQUENCE public.raw_macro_indicators_id_seq OWNED BY public.raw_macro_indicators.id;


--
-- Name: raw_sector_prices_id_seq; Type: SEQUENCE; Schema: public; Owner: sloanatkins
--

CREATE SEQUENCE public.raw_sector_prices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.raw_sector_prices_id_seq OWNER TO postgres;

--
-- Name: raw_sector_prices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sloanatkins
--

ALTER SEQUENCE public.raw_sector_prices_id_seq OWNED BY public.raw_sector_prices.id;


--
-- Name: raw_macro_indicators id; Type: DEFAULT; Schema: public; Owner: sloanatkins
--

ALTER TABLE ONLY public.raw_macro_indicators ALTER COLUMN id SET DEFAULT nextval('public.raw_macro_indicators_id_seq'::regclass);


--
-- Name: raw_sector_prices id; Type: DEFAULT; Schema: public; Owner: sloanatkins
--

ALTER TABLE ONLY public.raw_sector_prices ALTER COLUMN id SET DEFAULT nextval('public.raw_sector_prices_id_seq'::regclass);


--
-- Name: raw_macro_indicators raw_macro_indicators_pkey; Type: CONSTRAINT; Schema: public; Owner: sloanatkins
--

ALTER TABLE ONLY public.raw_macro_indicators
    ADD CONSTRAINT raw_macro_indicators_pkey PRIMARY KEY (id);


--
-- Name: raw_macro_indicators raw_macro_indicators_series_id_date_key; Type: CONSTRAINT; Schema: public; Owner: sloanatkins
--

ALTER TABLE ONLY public.raw_macro_indicators
    ADD CONSTRAINT raw_macro_indicators_series_id_date_key UNIQUE (series_id, date);


--
-- Name: raw_sector_prices raw_sector_prices_pkey; Type: CONSTRAINT; Schema: public; Owner: sloanatkins
--

ALTER TABLE ONLY public.raw_sector_prices
    ADD CONSTRAINT raw_sector_prices_pkey PRIMARY KEY (id);


--
-- Name: raw_sector_prices raw_sector_prices_symbol_date_key; Type: CONSTRAINT; Schema: public; Owner: sloanatkins
--

ALTER TABLE ONLY public.raw_sector_prices
    ADD CONSTRAINT raw_sector_prices_symbol_date_key UNIQUE (symbol, date);


--
-- PostgreSQL database dump complete
--

\unrestrict pSU1OaIzl5RnI01h9EkoVuhcDOEtmS51wKilHvxoE5RVrcBGh12a4k3KkpJTZNg

