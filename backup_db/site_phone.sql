PGDMP     .                    {            shop_dj_db_2    14.3    14.3     9           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            :           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            ;           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            <           1262    78766    shop_dj_db_2    DATABASE     a   CREATE DATABASE shop_dj_db_2 WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE = 'ru_UA.UTF-8';
    DROP DATABASE shop_dj_db_2;
                shop_dj_admin    false            6           1259    79661    main_page_sitephone    TABLE     �   CREATE TABLE public.main_page_sitephone (
    id bigint NOT NULL,
    "position" integer,
    phone_id bigint NOT NULL,
    CONSTRAINT main_page_sitephone_position_check CHECK (("position" >= 0))
);
 '   DROP TABLE public.main_page_sitephone;
       public         heap    shop_dj_admin    false            5           1259    79660    main_page_sitephone_id_seq    SEQUENCE     �   ALTER TABLE public.main_page_sitephone ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.main_page_sitephone_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          shop_dj_admin    false    310            6          0    79661    main_page_sitephone 
   TABLE DATA           G   COPY public.main_page_sitephone (id, "position", phone_id) FROM stdin;
    public          shop_dj_admin    false    310          =           0    0    main_page_sitephone_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.main_page_sitephone_id_seq', 2, true);
          public          shop_dj_admin    false    309            �           2606    79666 ,   main_page_sitephone main_page_sitephone_pkey 
   CONSTRAINT     j   ALTER TABLE ONLY public.main_page_sitephone
    ADD CONSTRAINT main_page_sitephone_pkey PRIMARY KEY (id);
 V   ALTER TABLE ONLY public.main_page_sitephone DROP CONSTRAINT main_page_sitephone_pkey;
       public            shop_dj_admin    false    310            �           1259    79715 %   main_page_sitephone_phone_id_c32ea370    INDEX     i   CREATE INDEX main_page_sitephone_phone_id_c32ea370 ON public.main_page_sitephone USING btree (phone_id);
 9   DROP INDEX public.main_page_sitephone_phone_id_c32ea370;
       public            shop_dj_admin    false    310            �           2606    79710 M   main_page_sitephone main_page_sitephone_phone_id_c32ea370_fk_ROOTAPP_phone_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.main_page_sitephone
    ADD CONSTRAINT "main_page_sitephone_phone_id_c32ea370_fk_ROOTAPP_phone_id" FOREIGN KEY (phone_id) REFERENCES public."ROOTAPP_phone"(id) DEFERRABLE INITIALLY DEFERRED;
 y   ALTER TABLE ONLY public.main_page_sitephone DROP CONSTRAINT "main_page_sitephone_phone_id_c32ea370_fk_ROOTAPP_phone_id";
       public          shop_dj_admin    false    310            6      x�3�4�4�2�B�=... *
     